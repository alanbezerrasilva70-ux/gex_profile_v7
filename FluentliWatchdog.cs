#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.Tools;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using SharpDX;
using SharpDX.Direct2D1;
using SharpDX.DirectWrite;
#endregion

namespace NinjaTrader.NinjaScript.Indicators
{
    public class FluentliWatchdog : Indicator
    {
        private enum IcebergKind
        {
            Dinamico = 1,
            Sintetico = 2
        }

        private class DepthSlot
        {
            public double Price;
            public long Volume;
        }

        private class PriceCluster
        {
            public double Price;
            public bool IsSellSide;
            public DateTime StartTime;
            public DateTime LastTradeTime;
            public long ExecutedVol;
            public int TradeCount;
            public int ReloadCount;
            public long ReloadAddedVol;
            public int SpokenTier;
            public IcebergEvent ActiveEvent;
        }

        private class IcebergEvent
        {
            public int BarIndex;
            public double Price;
            public long Volume;
            public bool IsSellSide;
            public IcebergKind Kind;
            public DateTime Timestamp;
            public bool TrackActive;
            public bool TrackCompleted;
            public int TrackEndBarIndex;
            public int FollowUpCount;
        }

        private readonly object syncLock = new object();
        private readonly Dictionary<int, DepthSlot> askSlots = new Dictionary<int, DepthSlot>();
        private readonly Dictionary<int, DepthSlot> bidSlots = new Dictionary<int, DepthSlot>();
        private readonly Dictionary<double, long> askDepthByPrice = new Dictionary<double, long>();
        private readonly Dictionary<double, long> bidDepthByPrice = new Dictionary<double, long>();
        private readonly Dictionary<string, PriceCluster> clusters = new Dictionary<string, PriceCluster>();
        private readonly List<IcebergEvent> events = new List<IcebergEvent>(512);
        private readonly List<IcebergEvent> visibleScratch = new List<IcebergEvent>(128);
        private readonly List<IcebergEvent> visibleTrackScratch = new List<IcebergEvent>(64);
        private readonly List<SharpDX.RectangleF> usedLabelRects = new List<SharpDX.RectangleF>(128);

        private double lastBid = 0;
        private double lastAsk = 0;
        private DateTime lastMarketTime = DateTime.MinValue;
        private object speechEngine;
        private Type speechType;
        private bool speechIsManaged;
        private DateTime lastVoiceTime = DateTime.MinValue;
        private string lastColorSignature = "";

        private SharpDX.DirectWrite.Factory dxFactory;
        private SharpDX.DirectWrite.TextFormat dxFont;
        private SharpDX.Direct2D1.StrokeStyle dxStrokeDash, dxStrokeDot;
        private SharpDX.Direct2D1.SolidColorBrush dxBuyDinFill, dxBuyDinAura, dxBuyDinBorder, dxBuyDinTrack, dxBuyDinGhost;
        private SharpDX.Direct2D1.SolidColorBrush dxSellDinFill, dxSellDinAura, dxSellDinBorder, dxSellDinTrack, dxSellDinGhost;
        private SharpDX.Direct2D1.SolidColorBrush dxBuySinRing, dxBuySinCenter, dxBuySinAura, dxBuySinTrack, dxBuySinGhost;
        private SharpDX.Direct2D1.SolidColorBrush dxSellSinRing, dxSellSinCenter, dxSellSinAura, dxSellSinTrack, dxSellSinGhost;
        private SharpDX.Direct2D1.SolidColorBrush dxLabelBg, dxTextBrush, dxLeaderBrush;

        [NinjaScriptProperty]
        [Range(1, 10000)]
        [Display(Name = "1. Lote Pequeno (Min)", GroupName = "1. Configuração de Lotes", Order = 1)]
        public int LotePequeno { get; set; }

        [NinjaScriptProperty]
        [Range(1, 10000)]
        [Display(Name = "2. Lote Médio", GroupName = "1. Configuração de Lotes", Order = 2)]
        public int LoteMedio { get; set; }

        [NinjaScriptProperty]
        [Range(1, 10000)]
        [Display(Name = "3. Lote Gigante (Tubarão)", GroupName = "1. Configuração de Lotes", Order = 3)]
        public int LoteGigante { get; set; }

        [NinjaScriptProperty]
        [Range(2, 120)]
        [Display(Name = "4. Janela Iceberg Sintético (seg)", GroupName = "1. Configuração de Lotes", Order = 4)]
        public int JanelaSinteticoSeg { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Mostrar Volume Real (Números)", GroupName = "2. Visual e Áudio", Order = 1)]
        public bool MostrarNumeros { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Ativar Alerta de Voz Dinâmico", GroupName = "2. Visual e Áudio", Order = 2)]
        public bool AtivarVoz { get; set; }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "1. Cor Iceberg Compra (Dinâmico)", GroupName = "3. Cores Personalizadas", Order = 1)]
        public System.Windows.Media.Brush CorCompraDinamico { get; set; }

        [Browsable(false)]
        public string CorCompraDinamicoSerialize
        {
            get { return Serialize.BrushToString(CorCompraDinamico ?? System.Windows.Media.Brushes.MediumSpringGreen); }
            set { if (!string.IsNullOrEmpty(value)) CorCompraDinamico = Serialize.StringToBrush(value); }
        }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "2. Cor Iceberg Venda (Dinâmico)", GroupName = "3. Cores Personalizadas", Order = 2)]
        public System.Windows.Media.Brush CorVendaDinamico { get; set; }

        [Browsable(false)]
        public string CorVendaDinamicoSerialize
        {
            get { return Serialize.BrushToString(CorVendaDinamico ?? System.Windows.Media.Brushes.Crimson); }
            set { if (!string.IsNullOrEmpty(value)) CorVendaDinamico = Serialize.StringToBrush(value); }
        }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "3. Cor Iceberg Compra (Sintético)", GroupName = "3. Cores Personalizadas", Order = 3)]
        public System.Windows.Media.Brush CorCompraSintetico { get; set; }

        [Browsable(false)]
        public string CorCompraSinteticoSerialize
        {
            get { return Serialize.BrushToString(CorCompraSintetico ?? System.Windows.Media.Brushes.Cyan); }
            set { if (!string.IsNullOrEmpty(value)) CorCompraSintetico = Serialize.StringToBrush(value); }
        }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "4. Cor Iceberg Venda (Sintético)", GroupName = "3. Cores Personalizadas", Order = 4)]
        public System.Windows.Media.Brush CorVendaSintetico { get; set; }

        [Browsable(false)]
        public string CorVendaSinteticoSerialize
        {
            get { return Serialize.BrushToString(CorVendaSintetico ?? System.Windows.Media.Brushes.DarkOrange); }
            set { if (!string.IsNullOrEmpty(value)) CorVendaSintetico = Serialize.StringToBrush(value); }
        }

        [NinjaScriptProperty]
        [Display(Name = "Ativar Linha Rastreio de Defesa", GroupName = "4. Rastreio de Defesa no Preço", Order = 1)]
        public bool AtivarLinhaRastreio { get; set; }

        [NinjaScriptProperty]
        [Range(1, 50000)]
        [Display(Name = "Lote Mínimo para Linha Rastreio", GroupName = "4. Rastreio de Defesa no Preço", Order = 2)]
        public int RastreioLoteMinimo { get; set; }

        [NinjaScriptProperty]
        [Range(1, 200)]
        [Display(Name = "Tolerância Rompimento (Ticks)", GroupName = "4. Rastreio de Defesa no Preço", Order = 3)]
        public int ToleranciaRastreioTicks { get; set; }

        [NinjaScriptProperty]
        [Range(1, 25)]
        [Display(Name = "Máx. Linhas Ativas Simultâneas", GroupName = "4. Rastreio de Defesa no Preço", Order = 4)]
        public int MaxLinhasRastreio { get; set; }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"Rastreador Institucional de Icebergs Dinâmicos (DOM Reload), Sintéticos (Fracionados) e Rastreio de Defesa no Preço";
                Name = "FluentliWatchdog";
                Calculate = Calculate.OnEachTick;
                IsOverlay = true;
                DrawOnPricePanel = true;
                DisplayInDataBox = false;
                ScaleJustification = NinjaTrader.Gui.Chart.ScaleJustification.Right;

                LotePequeno = 50;
                LoteMedio = 250;
                LoteGigante = 500;
                JanelaSinteticoSeg = 15;
                MostrarNumeros = true;
                AtivarVoz = true;

                CorCompraDinamico = System.Windows.Media.Brushes.MediumSpringGreen;
                CorVendaDinamico = System.Windows.Media.Brushes.Crimson;
                CorCompraSintetico = System.Windows.Media.Brushes.Cyan;
                CorVendaSintetico = System.Windows.Media.Brushes.DarkOrange;

                AtivarLinhaRastreio = true;
                RastreioLoteMinimo = 100;
                ToleranciaRastreioTicks = 8;
                MaxLinhasRastreio = 6;
            }
            else if (State == State.DataLoaded)
            {
                InitSpeech();
            }
            else if (State == State.Terminated)
            {
                LimparRecursosRender();
                DisposeSpeech();
            }
        }

        private void InitSpeech()
        {
            if (speechEngine != null) return;
            try
            {
                Assembly asm = Assembly.Load("System.Speech, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35");
                Type t = (asm != null) ? asm.GetType("System.Speech.Synthesis.SpeechSynthesizer") : null;
                if (t != null)
                {
                    object eng = Activator.CreateInstance(t);
                    t.InvokeMember("SetOutputToDefaultAudioDevice", BindingFlags.InvokeMethod, null, eng, null);
                    t.InvokeMember("Volume", BindingFlags.SetProperty, null, eng, new object[] { 100 });
                    speechType = t;
                    speechEngine = eng;
                    speechIsManaged = true;
                    return;
                }
            }
            catch { }

            try
            {
                Type comType = Type.GetTypeFromProgID("SAPI.SpVoice");
                if (comType != null)
                {
                    object comVoice = Activator.CreateInstance(comType);
                    comType.InvokeMember("Volume", BindingFlags.SetProperty, null, comVoice, new object[] { 100 });
                    speechType = comType;
                    speechEngine = comVoice;
                    speechIsManaged = false;
                }
            }
            catch { }
        }

        private void SpeakAlertAsync(string msg)
        {
            if (string.IsNullOrEmpty(msg)) return;
            if (speechEngine == null) InitSpeech();
            if (speechEngine == null || speechType == null) return;
            try
            {
                if (speechIsManaged)
                    speechType.InvokeMember("SpeakAsync", BindingFlags.InvokeMethod, null, speechEngine, new object[] { msg });
                else
                    speechType.InvokeMember("Speak", BindingFlags.InvokeMethod, null, speechEngine, new object[] { msg, 3 });
            }
            catch { }
        }

        private void DisposeSpeech()
        {
            if (speechEngine == null) return;
            try
            {
                if (speechIsManaged && speechType != null)
                {
                    try { speechType.InvokeMember("SpeakAsyncCancelAll", BindingFlags.InvokeMethod, null, speechEngine, null); } catch { }
                    try { speechType.InvokeMember("Dispose", BindingFlags.InvokeMethod, null, speechEngine, null); } catch { }
                }
                else if (Marshal.IsComObject(speechEngine))
                {
                    Marshal.ReleaseComObject(speechEngine);
                }
            }
            catch { }
            speechEngine = null;
            speechType = null;
        }

        protected override void OnBarUpdate()
        {
        }

        private double GetTolerancePrice()
        {
            double tickSz = (TickSize > 0) ? TickSize : 0.25;
            int ticks = (ToleranciaRastreioTicks >= 1) ? ToleranciaRastreioTicks : 8;
            return ticks * tickSz;
        }

        private void AtualizarLinhasRastreio(double preco, int barIdx)
        {
            if (!AtivarLinhaRastreio) return;
            double tol = GetTolerancePrice();
            for (int i = 0; i < events.Count; i++)
            {
                IcebergEvent ev = events[i];
                if (!ev.TrackActive) continue;

                bool rompeu = ev.IsSellSide
                    ? (preco > ev.Price + tol)
                    : (preco < ev.Price - tol);

                ev.TrackEndBarIndex = Math.Max(ev.TrackEndBarIndex, barIdx);
                if (rompeu)
                {
                    ev.TrackActive = false;
                    ev.TrackCompleted = true;
                }
            }
        }

        private void TentarAtivarRastreio(IcebergEvent ev, int barIdx)
        {
            if (!AtivarLinhaRastreio) return;
            int minLote = Math.Max(1, RastreioLoteMinimo);
            if (ev.Volume < minLote || ev.TrackCompleted || ev.TrackActive) return;

            double tolZona = GetTolerancePrice() * 4.0;
            for (int i = 0; i < events.Count; i++)
            {
                IcebergEvent parent = events[i];
                if (parent == ev || !parent.TrackActive) continue;
                if (parent.IsSellSide == ev.IsSellSide && Math.Abs(parent.Price - ev.Price) <= tolZona)
                {
                    parent.FollowUpCount++;
                    parent.TrackEndBarIndex = Math.Max(parent.TrackEndBarIndex, barIdx);
                }
            }

            ev.TrackActive = true;
            ev.TrackEndBarIndex = Math.Max(ev.TrackEndBarIndex, barIdx);

            int maxLines = Math.Max(1, MaxLinhasRastreio);
            int activeCount = 0;
            for (int i = 0; i < events.Count; i++)
            {
                if (events[i].TrackActive) activeCount++;
            }

            if (activeCount > maxLines)
            {
                for (int i = 0; i < events.Count && activeCount > maxLines; i++)
                {
                    if (events[i].TrackActive && events[i] != ev)
                    {
                        events[i].TrackActive = false;
                        events[i].TrackCompleted = true;
                        activeCount--;
                    }
                }
            }
        }

        private void AtualizarLivro(Dictionary<int, DepthSlot> slots, Dictionary<double, long> depthMap, MarketDepthEventArgs e, bool isSellSide)
        {
            DepthSlot prev;
            double oldPrice = 0;
            long oldVol = 0;
            bool hadPrev = slots.TryGetValue(e.Position, out prev);
            if (hadPrev)
            {
                oldPrice = prev.Price;
                oldVol = prev.Volume;
                long existing;
                if (depthMap.TryGetValue(oldPrice, out existing))
                {
                    long updated = Math.Max(0, existing - oldVol);
                    if (updated == 0) depthMap.Remove(oldPrice);
                    else depthMap[oldPrice] = updated;
                }
            }

            if (e.Operation == NinjaTrader.Cbi.Operation.Remove)
            {
                if (hadPrev) slots.Remove(e.Position);
                return;
            }

            if (!hadPrev)
            {
                prev = new DepthSlot();
                slots[e.Position] = prev;
            }
            prev.Price = e.Price;
            prev.Volume = e.Volume;

            long cur;
            depthMap.TryGetValue(e.Price, out cur);
            depthMap[e.Price] = cur + e.Volume;

            // Recarregamento passivo no DOM: mesma posição e preço subiu de lote durante agressões (Live e Market Replay)
            if (e.Operation == NinjaTrader.Cbi.Operation.Update && hadPrev && Math.Abs(oldPrice - e.Price) < 1e-9 && e.Volume > oldVol)
            {
                string key = (isSellSide ? "S_" : "B_") + e.Price.ToString("G17", System.Globalization.CultureInfo.InvariantCulture);
                PriceCluster cl;
                DateTime refTime = (e.Time != DateTime.MinValue) ? e.Time : ((lastMarketTime != DateTime.MinValue) ? lastMarketTime : DateTime.Now);
                if (clusters.TryGetValue(key, out cl) && (refTime - cl.LastTradeTime).TotalSeconds <= 5.0)
                {
                    cl.ReloadCount++;
                    cl.ReloadAddedVol += (e.Volume - oldVol);
                }
            }
        }

        protected override void OnMarketDepth(MarketDepthEventArgs e)
        {
            if (e == null) return;
            lock (syncLock)
            {
                if (e.MarketDataType == MarketDataType.Ask)
                    AtualizarLivro(askSlots, askDepthByPrice, e, true);
                else if (e.MarketDataType == MarketDataType.Bid)
                    AtualizarLivro(bidSlots, bidDepthByPrice, e, false);
            }
        }

        protected override void OnMarketData(MarketDataEventArgs e)
        {
            if (e == null) return;

            if (e.MarketDataType == MarketDataType.Bid)
            {
                lastBid = e.Price;
                return;
            }
            if (e.MarketDataType == MarketDataType.Ask)
            {
                lastAsk = e.Price;
                return;
            }
            if (e.MarketDataType != MarketDataType.Last || e.Volume <= 0)
                return;

            if (e.Time != DateTime.MinValue) lastMarketTime = e.Time;
            if (CurrentBar < 0) return;

            double preco = e.Price;
            long agressao = e.Volume;
            double curBid = (e.Bid > 0) ? e.Bid : lastBid;
            double curAsk = (e.Ask > 0) ? e.Ask : lastAsk;

            bool icebergDeVenda;
            if (curAsk > 0 && curBid > 0)
            {
                if (preco >= curAsk) icebergDeVenda = true;
                else if (preco <= curBid) icebergDeVenda = false;
                else icebergDeVenda = (preco - curBid) >= (curAsk - preco);
            }
            else
            {
                icebergDeVenda = preco >= Close[0];
            }

            int safeJanela = (JanelaSinteticoSeg >= 2 && JanelaSinteticoSeg <= 120) ? JanelaSinteticoSeg : 15;
            string voiceMsg = null;
            int barIdx = CurrentBar;

            lock (syncLock)
            {
                AtualizarLinhasRastreio(preco, barIdx);

                string key = (icebergDeVenda ? "S_" : "B_") + preco.ToString("G17", System.Globalization.CultureInfo.InvariantCulture);
                PriceCluster cl;
                if (!clusters.TryGetValue(key, out cl))
                {
                    cl = new PriceCluster
                    {
                        Price = preco,
                        IsSellSide = icebergDeVenda,
                        StartTime = e.Time,
                        LastTradeTime = e.Time
                    };
                    clusters[key] = cl;
                }

                if ((e.Time - cl.StartTime).TotalSeconds > safeJanela)
                {
                    cl.StartTime = e.Time;
                    cl.ExecutedVol = 0;
                    cl.TradeCount = 0;
                    cl.ReloadCount = 0;
                    cl.ReloadAddedVol = 0;
                    cl.SpokenTier = 0;
                    cl.ActiveEvent = null;
                }

                cl.LastTradeTime = e.Time;
                cl.ExecutedVol += agressao;
                cl.TradeCount++;

                Dictionary<double, long> depthMap = icebergDeVenda ? askDepthByPrice : bidDepthByPrice;
                bool hasDepthData = depthMap.Count > 0;
                long visibleDepth = 0;
                depthMap.TryGetValue(preco, out visibleDepth);

                bool isDinamico =
                    (cl.ReloadCount >= 2 && cl.ExecutedVol >= LotePequeno) ||
                    (hasDepthData && agressao >= LotePequeno && agressao > visibleDepth) ||
                    (!hasDepthData && agressao >= LotePequeno);

                bool isSintetico = !isDinamico && cl.TradeCount >= 2 && cl.ExecutedVol >= LotePequeno;

                if (!isDinamico && !isSintetico)
                    return;

                IcebergKind detectedKind = isDinamico ? IcebergKind.Dinamico : IcebergKind.Sintetico;

                if (cl.ActiveEvent != null && cl.ActiveEvent.BarIndex == barIdx)
                {
                    cl.ActiveEvent.Volume = cl.ExecutedVol;
                    cl.ActiveEvent.Timestamp = e.Time;
                    if (detectedKind == IcebergKind.Dinamico) cl.ActiveEvent.Kind = IcebergKind.Dinamico;
                    TentarAtivarRastreio(cl.ActiveEvent, barIdx);
                }
                else
                {
                    IcebergEvent ev = new IcebergEvent
                    {
                        BarIndex = barIdx,
                        Price = preco,
                        Volume = cl.ExecutedVol,
                        IsSellSide = icebergDeVenda,
                        Kind = detectedKind,
                        Timestamp = e.Time,
                        TrackEndBarIndex = barIdx
                    };
                    events.Add(ev);
                    cl.ActiveEvent = ev;
                    TentarAtivarRastreio(ev, barIdx);

                    if (events.Count > 450)
                        events.RemoveRange(0, events.Count - 400);
                }

                int tier = (cl.ExecutedVol >= LoteGigante) ? 3 : ((cl.ExecutedVol >= LoteMedio) ? 2 : 1);
                if (tier > cl.SpokenTier)
                {
                    cl.SpokenTier = tier;
                    string tipoTxt = (cl.ActiveEvent.Kind == IcebergKind.Dinamico) ? "Dinâmico" : "Sintético";
                    string ladoTxt = icebergDeVenda ? "Venda" : "Compra";
                    if (tier == 3) voiceMsg = "Iceberg " + tipoTxt + " Gigante de " + ladoTxt;
                    else if (tier == 2) voiceMsg = "Iceberg " + tipoTxt + " Médio de " + ladoTxt;
                    else voiceMsg = "Absorção " + tipoTxt + " de " + ladoTxt;
                }
            }

            if (voiceMsg != null && AtivarVoz)
            {
                if ((DateTime.Now - lastVoiceTime).TotalSeconds >= 4.0)
                {
                    lastVoiceTime = DateTime.Now;
                    SpeakAlertAsync(voiceMsg);
                }
            }
        }

        private Color4 ExtractColor4(System.Windows.Media.Brush wpfBrush, Color4 fallback, float alphaOverride)
        {
            System.Windows.Media.SolidColorBrush scb = wpfBrush as System.Windows.Media.SolidColorBrush;
            if (scb != null)
            {
                System.Windows.Media.Color c = scb.Color;
                return new Color4(c.R / 255f, c.G / 255f, c.B / 255f, alphaOverride);
            }
            return new Color4(fallback.Red, fallback.Green, fallback.Blue, alphaOverride);
        }

        private Color4 LightenColor4(Color4 c, float boost, float alphaOverride)
        {
            return new Color4(
                Math.Min(1.0f, c.Red + boost),
                Math.Min(1.0f, c.Green + boost),
                Math.Min(1.0f, c.Blue + boost),
                alphaOverride
            );
        }

        private string ColorKeyPart(System.Windows.Media.Brush wpfBrush)
        {
            System.Windows.Media.SolidColorBrush scb = wpfBrush as System.Windows.Media.SolidColorBrush;
            if (scb == null) return "default";
            System.Windows.Media.Color c = scb.Color;
            return c.R + "," + c.G + "," + c.B;
        }

        private void EnsureRenderResources()
        {
            string sig = ColorKeyPart(CorCompraDinamico) + "|" + ColorKeyPart(CorVendaDinamico) + "|" + ColorKeyPart(CorCompraSintetico) + "|" + ColorKeyPart(CorVendaSintetico);
            if (!string.IsNullOrEmpty(lastColorSignature) && lastColorSignature != sig)
            {
                LimparRecursosRender();
            }
            lastColorSignature = sig;

            if (dxFactory == null) dxFactory = new SharpDX.DirectWrite.Factory();
            if (dxFont == null) dxFont = new SharpDX.DirectWrite.TextFormat(dxFactory, "Consolas", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 10f);

            if (dxStrokeDash == null)
            {
                dxStrokeDash = new SharpDX.Direct2D1.StrokeStyle(
                    NinjaTrader.Core.Globals.D2DFactory,
                    new SharpDX.Direct2D1.StrokeStyleProperties { DashStyle = SharpDX.Direct2D1.DashStyle.Dash }
                );
            }
            if (dxStrokeDot == null)
            {
                dxStrokeDot = new SharpDX.Direct2D1.StrokeStyle(
                    NinjaTrader.Core.Globals.D2DFactory,
                    new SharpDX.Direct2D1.StrokeStyleProperties { DashStyle = SharpDX.Direct2D1.DashStyle.Dot }
                );
            }

            Color4 cBuyDin = ExtractColor4(CorCompraDinamico, new Color4(0.10f, 0.88f, 0.56f, 1f), 1f);
            Color4 cSellDin = ExtractColor4(CorVendaDinamico, new Color4(0.95f, 0.22f, 0.36f, 1f), 1f);
            Color4 cBuySin = ExtractColor4(CorCompraSintetico, new Color4(0.16f, 0.94f, 0.84f, 1f), 1f);
            Color4 cSellSin = ExtractColor4(CorVendaSintetico, new Color4(1.00f, 0.54f, 0.16f, 1f), 1f);

            if (dxBuyDinFill == null) dxBuyDinFill = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuyDin.Red, cBuyDin.Green, cBuyDin.Blue, 0.78f));
            if (dxBuyDinAura == null) dxBuyDinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuyDin.Red, cBuyDin.Green, cBuyDin.Blue, 0.18f));
            if (dxBuyDinBorder == null) dxBuyDinBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, LightenColor4(cBuyDin, 0.18f, 0.98f));
            if (dxBuyDinTrack == null) dxBuyDinTrack = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuyDin.Red, cBuyDin.Green, cBuyDin.Blue, 0.82f));
            if (dxBuyDinGhost == null) dxBuyDinGhost = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuyDin.Red, cBuyDin.Green, cBuyDin.Blue, 0.34f));

            if (dxSellDinFill == null) dxSellDinFill = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellDin.Red, cSellDin.Green, cSellDin.Blue, 0.78f));
            if (dxSellDinAura == null) dxSellDinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellDin.Red, cSellDin.Green, cSellDin.Blue, 0.18f));
            if (dxSellDinBorder == null) dxSellDinBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, LightenColor4(cSellDin, 0.18f, 0.98f));
            if (dxSellDinTrack == null) dxSellDinTrack = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellDin.Red, cSellDin.Green, cSellDin.Blue, 0.82f));
            if (dxSellDinGhost == null) dxSellDinGhost = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellDin.Red, cSellDin.Green, cSellDin.Blue, 0.34f));

            if (dxBuySinRing == null) dxBuySinRing = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red, cBuySin.Green, cBuySin.Blue, 0.98f));
            if (dxBuySinCenter == null) dxBuySinCenter = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red * 0.15f, cBuySin.Green * 0.18f, cBuySin.Blue * 0.18f, 0.86f));
            if (dxBuySinAura == null) dxBuySinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red, cBuySin.Green, cBuySin.Blue, 0.16f));
            if (dxBuySinTrack == null) dxBuySinTrack = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red, cBuySin.Green, cBuySin.Blue, 0.82f));
            if (dxBuySinGhost == null) dxBuySinGhost = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red, cBuySin.Green, cBuySin.Blue, 0.34f));

            if (dxSellSinRing == null) dxSellSinRing = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red, cSellSin.Green, cSellSin.Blue, 0.98f));
            if (dxSellSinCenter == null) dxSellSinCenter = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red * 0.18f, cSellSin.Green * 0.12f, cSellSin.Blue * 0.10f, 0.86f));
            if (dxSellSinAura == null) dxSellSinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red, cSellSin.Green, cSellSin.Blue, 0.16f));
            if (dxSellSinTrack == null) dxSellSinTrack = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red, cSellSin.Green, cSellSin.Blue, 0.82f));
            if (dxSellSinGhost == null) dxSellSinGhost = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red, cSellSin.Green, cSellSin.Blue, 0.34f));

            if (dxLabelBg == null) dxLabelBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.03f, 0.05f, 0.09f, 0.92f));
            if (dxTextBrush == null) dxTextBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.95f, 0.97f, 1.00f, 1.00f));
            if (dxLeaderBrush == null) dxLeaderBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.70f, 0.78f, 0.90f, 0.55f));
        }

        private bool LabelColide(SharpDX.RectangleF cand)
        {
            for (int i = 0; i < usedLabelRects.Count; i++)
            {
                SharpDX.RectangleF b = usedLabelRects[i];
                if (cand.Left < b.Right && cand.Right > b.Left && cand.Top < b.Bottom && cand.Bottom > b.Top)
                    return true;
            }
            return false;
        }

        private float ResolveNonCollidingTop(float boxLeft, float targetCenterY, float pillW, float pillH, float panelTop, float panelBottom)
        {
            float chosenTop = Math.Max(panelTop + 4f, Math.Min(panelBottom - pillH - 4f, targetCenterY - pillH * 0.5f));
            if (!LabelColide(new SharpDX.RectangleF(boxLeft - 2f, chosenTop - 1f, pillW + 4f, pillH + 2f)))
                return chosenTop;

            float[] offsets = { -17f, 17f, -34f, 34f, -51f, 51f };
            foreach (float dy in offsets)
            {
                float candTop = Math.Max(panelTop + 4f, Math.Min(panelBottom - pillH - 4f, (targetCenterY + dy) - pillH * 0.5f));
                if (!LabelColide(new SharpDX.RectangleF(boxLeft - 2f, candTop - 1f, pillW + 4f, pillH + 2f)))
                    return candTop;
            }
            return chosenTop;
        }

        private void DrawPillText(string txt, float boxLeft, float chosenTop, float pillW, float pillH, SharpDX.Direct2D1.SolidColorBrush borderBrush)
        {
            SharpDX.RectangleF pillRect = new SharpDX.RectangleF(boxLeft, chosenTop, pillW, pillH);
            usedLabelRects.Add(new SharpDX.RectangleF(boxLeft - 2f, chosenTop - 1f, pillW + 4f, pillH + 2f));
            SharpDX.Direct2D1.RoundedRectangle pill = new SharpDX.Direct2D1.RoundedRectangle { Rect = pillRect, RadiusX = 3.5f, RadiusY = 3.5f };
            RenderTarget.FillRoundedRectangle(pill, dxLabelBg);
            RenderTarget.DrawRoundedRectangle(pill, borderBrush, 0.9f);
            RenderTarget.DrawText(txt, dxFont, new SharpDX.RectangleF(boxLeft + 5f, chosenTop + 1.5f, pillW - 6f, pillH - 1f), borderBrush);
        }

        private SharpDX.Direct2D1.SolidColorBrush ResolveAccentBrush(IcebergEvent ev, bool ghostTrack)
        {
            if (ev.Kind == IcebergKind.Dinamico)
            {
                if (ghostTrack) return ev.IsSellSide ? dxSellDinGhost : dxBuyDinGhost;
                return ev.IsSellSide ? dxSellDinBorder : dxBuyDinBorder;
            }
            if (ghostTrack) return ev.IsSellSide ? dxSellSinGhost : dxBuySinGhost;
            return ev.IsSellSide ? dxSellSinRing : dxBuySinRing;
        }

        private SharpDX.Direct2D1.SolidColorBrush ResolveTrackBrush(IcebergEvent ev)
        {
            if (ev.Kind == IcebergKind.Dinamico)
            {
                if (ev.TrackActive) return ev.IsSellSide ? dxSellDinTrack : dxBuyDinTrack;
                return ev.IsSellSide ? dxSellDinGhost : dxBuyDinGhost;
            }
            if (ev.TrackActive) return ev.IsSellSide ? dxSellSinTrack : dxBuySinTrack;
            return ev.IsSellSide ? dxSellSinGhost : dxBuySinGhost;
        }

        protected override void OnRender(ChartControl chartControl, ChartScale chartScale)
        {
            if (chartControl == null || chartScale == null || ChartBars == null || ChartPanel == null || RenderTarget == null)
                return;

            visibleScratch.Clear();
            visibleTrackScratch.Clear();
            int fromIdx = Math.Max(0, ChartBars.FromIndex);
            int toIdx = ChartBars.ToIndex;

            lock (syncLock)
            {
                for (int i = 0; i < events.Count; i++)
                {
                    IcebergEvent ev = events[i];
                    if (ev.BarIndex >= fromIdx && ev.BarIndex <= toIdx)
                        visibleScratch.Add(ev);

                    if (AtivarLinhaRastreio && (ev.TrackActive || ev.TrackCompleted))
                    {
                        int endIdx = ev.TrackActive ? Math.Max(ev.TrackEndBarIndex, toIdx) : ev.TrackEndBarIndex;
                        if (endIdx >= fromIdx && ev.BarIndex <= toIdx)
                            visibleTrackScratch.Add(ev);
                    }
                }
            }

            if (visibleScratch.Count == 0 && visibleTrackScratch.Count == 0) return;

            EnsureRenderResources();
            usedLabelRects.Clear();
            SharpDX.Direct2D1.AntialiasMode prevAa = RenderTarget.AntialiasMode;
            RenderTarget.AntialiasMode = SharpDX.Direct2D1.AntialiasMode.PerPrimitive;

            float panelLeft = (float)ChartPanel.X;
            float panelTop = (float)ChartPanel.Y;
            float panelRight = (float)(ChartPanel.X + ChartPanel.W);
            float panelBottom = (float)(ChartPanel.Y + ChartPanel.H);
            float rightAnchorX = (toIdx >= fromIdx)
                ? Math.Min(panelRight - 8f, (float)chartControl.GetXByBarIndex(ChartBars, toIdx) + 28f)
                : panelRight - 12f;

            // Passo 0: Linhas de Rastreio de Defesa no Preço (atrás das bolinhas)
            for (int i = 0; i < visibleTrackScratch.Count; i++)
            {
                IcebergEvent ev = visibleTrackScratch[i];
                float y = (float)chartScale.GetYByValue(ev.Price);
                if (y < panelTop + 2f || y > panelBottom - 2f) continue;

                float xStart = (ev.BarIndex < fromIdx)
                    ? panelLeft + 2f
                    : Math.Max(panelLeft + 2f, (float)chartControl.GetXByBarIndex(ChartBars, ev.BarIndex));

                float xEnd;
                if (ev.TrackActive)
                {
                    xEnd = rightAnchorX;
                }
                else
                {
                    int clampedEnd = Math.Max(fromIdx, Math.Min(toIdx, ev.TrackEndBarIndex));
                    xEnd = Math.Min(panelRight - 6f, (float)chartControl.GetXByBarIndex(ChartBars, clampedEnd));
                }

                if (xEnd <= xStart + 4f) continue;

                SharpDX.Direct2D1.SolidColorBrush lineBrush = ResolveTrackBrush(ev);
                if (ev.TrackActive)
                {
                    RenderTarget.DrawLine(new SharpDX.Vector2(xStart, y), new SharpDX.Vector2(xEnd, y), lineBrush, 1.35f, dxStrokeDash);
                    RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(new SharpDX.Vector2(xEnd, y), 2.8f, 2.8f), lineBrush);
                }
                else
                {
                    RenderTarget.DrawLine(new SharpDX.Vector2(xStart, y), new SharpDX.Vector2(xEnd, y), lineBrush, 0.9f, dxStrokeDot);
                    RenderTarget.DrawLine(new SharpDX.Vector2(xEnd - 3f, y - 3f), new SharpDX.Vector2(xEnd + 3f, y + 3f), lineBrush, 1.0f);
                    RenderTarget.DrawLine(new SharpDX.Vector2(xEnd - 3f, y + 3f), new SharpDX.Vector2(xEnd + 3f, y - 3f), lineBrush, 1.0f);
                }
            }

            double minVol = Math.Max(1.0, LotePequeno);
            double maxRef = Math.Max(minVol + 10.0, LoteGigante * 1.5);

            // Passo 1: Desenha todas as bolinhas proporcionais (Dinâmico sólido vs. Sintético anel)
            for (int i = 0; i < visibleScratch.Count; i++)
            {
                IcebergEvent ev = visibleScratch[i];
                float x = (float)chartControl.GetXByBarIndex(ChartBars, ev.BarIndex);
                float y = (float)chartScale.GetYByValue(ev.Price);
                if (y < panelTop - 30f || y > panelBottom + 30f || x < panelLeft - 30f || x > panelRight + 30f) continue;

                double norm = Math.Max(0.0, Math.Min(1.0, (ev.Volume - minVol) / (maxRef - minVol)));
                float radius = 6.5f + (float)(Math.Sqrt(norm) * 17.0);
                SharpDX.Vector2 center = new SharpDX.Vector2(x, y);

                if (ev.Kind == IcebergKind.Dinamico)
                {
                    RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(center, radius + 4.5f, radius + 4.5f), ev.IsSellSide ? dxSellDinAura : dxBuyDinAura);
                    RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(center, radius, radius), ev.IsSellSide ? dxSellDinFill : dxBuyDinFill);
                    RenderTarget.DrawEllipse(new SharpDX.Direct2D1.Ellipse(center, radius, radius), ev.IsSellSide ? dxSellDinBorder : dxBuyDinBorder, 1.4f);
                }
                else
                {
                    RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(center, radius + 4.0f, radius + 4.0f), ev.IsSellSide ? dxSellSinAura : dxBuySinAura);
                    RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(center, radius, radius), ev.IsSellSide ? dxSellSinCenter : dxBuySinCenter);
                    RenderTarget.DrawEllipse(new SharpDX.Direct2D1.Ellipse(center, radius, radius), ev.IsSellSide ? dxSellSinRing : dxBuySinRing, 2.3f);
                    if (radius >= 8f)
                        RenderTarget.DrawEllipse(new SharpDX.Direct2D1.Ellipse(center, radius * 0.50f, radius * 0.50f), ev.IsSellSide ? dxSellSinRing : dxBuySinRing, 1.1f);
                }
            }

            if (!MostrarNumeros)
            {
                RenderTarget.AntialiasMode = prevAa;
                return;
            }

            // Passo 2: Etiquetas das bolinhas (nunca em cima do círculo!) + etiquetas das defesas ativas
            for (int i = 0; i < visibleScratch.Count; i++)
            {
                IcebergEvent ev = visibleScratch[i];
                float x = (float)chartControl.GetXByBarIndex(ChartBars, ev.BarIndex);
                float y = (float)chartScale.GetYByValue(ev.Price);
                if (y < panelTop - 20f || y > panelBottom + 20f || x < panelLeft - 20f || x > panelRight + 20f) continue;

                double norm = Math.Max(0.0, Math.Min(1.0, (ev.Volume - minVol) / (maxRef - minVol)));
                float radius = 6.5f + (float)(Math.Sqrt(norm) * 17.0);

                string prefix = (ev.Kind == IcebergKind.Dinamico) ? "D " : "S ";
                string txt = prefix + ev.Volume.ToString();
                float pillW = Math.Max(34f, txt.Length * 6.5f + 10f);
                float pillH = 15f;

                float rightCandidateLeft = x + radius + 7f;
                float boxLeft = (rightCandidateLeft + pillW <= panelRight - 4f)
                    ? rightCandidateLeft
                    : Math.Max(panelLeft + 4f, x - radius - pillW - 7f);

                float chosenTop = ResolveNonCollidingTop(boxLeft, y, pillW, pillH, panelTop, panelBottom);
                float edgeX = (boxLeft > x) ? (x + radius + 1f) : (x - radius - 1f);
                float pillEdgeX = (boxLeft > x) ? boxLeft : (boxLeft + pillW);
                RenderTarget.DrawLine(new SharpDX.Vector2(edgeX, y), new SharpDX.Vector2(pillEdgeX, chosenTop + pillH * 0.5f), dxLeaderBrush, 0.85f);

                DrawPillText(txt, boxLeft, chosenTop, pillW, pillH, ResolveAccentBrush(ev, false));
            }

            for (int i = 0; i < visibleTrackScratch.Count; i++)
            {
                IcebergEvent ev = visibleTrackScratch[i];
                if (!ev.TrackActive) continue;
                float y = (float)chartScale.GetYByValue(ev.Price);
                if (y < panelTop + 4f || y > panelBottom - 4f) continue;

                string sideLabel = ev.IsSellSide ? "DEF V " : "DEF C ";
                string trackTxt = sideLabel + ev.Volume.ToString() + (ev.FollowUpCount > 0 ? " (+" + ev.FollowUpCount + ")" : "");
                float tW = Math.Max(60f, trackTxt.Length * 6.3f + 10f);
                float tH = 14f;
                float tLeft = Math.Max(panelLeft + 4f, Math.Min(panelRight - tW - 4f, rightAnchorX - tW));
                float tTop = ResolveNonCollidingTop(tLeft, y - 12f, tW, tH, panelTop, panelBottom);

                DrawPillText(trackTxt, tLeft, tTop, tW, tH, ResolveTrackBrush(ev));
            }

            RenderTarget.AntialiasMode = prevAa;
        }

        private void LimparRecursosRender()
        {
            if (dxBuyDinFill != null) { dxBuyDinFill.Dispose(); dxBuyDinFill = null; }
            if (dxBuyDinAura != null) { dxBuyDinAura.Dispose(); dxBuyDinAura = null; }
            if (dxBuyDinBorder != null) { dxBuyDinBorder.Dispose(); dxBuyDinBorder = null; }
            if (dxBuyDinTrack != null) { dxBuyDinTrack.Dispose(); dxBuyDinTrack = null; }
            if (dxBuyDinGhost != null) { dxBuyDinGhost.Dispose(); dxBuyDinGhost = null; }
            if (dxSellDinFill != null) { dxSellDinFill.Dispose(); dxSellDinFill = null; }
            if (dxSellDinAura != null) { dxSellDinAura.Dispose(); dxSellDinAura = null; }
            if (dxSellDinBorder != null) { dxSellDinBorder.Dispose(); dxSellDinBorder = null; }
            if (dxSellDinTrack != null) { dxSellDinTrack.Dispose(); dxSellDinTrack = null; }
            if (dxSellDinGhost != null) { dxSellDinGhost.Dispose(); dxSellDinGhost = null; }
            if (dxBuySinRing != null) { dxBuySinRing.Dispose(); dxBuySinRing = null; }
            if (dxBuySinCenter != null) { dxBuySinCenter.Dispose(); dxBuySinCenter = null; }
            if (dxBuySinAura != null) { dxBuySinAura.Dispose(); dxBuySinAura = null; }
            if (dxBuySinTrack != null) { dxBuySinTrack.Dispose(); dxBuySinTrack = null; }
            if (dxBuySinGhost != null) { dxBuySinGhost.Dispose(); dxBuySinGhost = null; }
            if (dxSellSinRing != null) { dxSellSinRing.Dispose(); dxSellSinRing = null; }
            if (dxSellSinCenter != null) { dxSellSinCenter.Dispose(); dxSellSinCenter = null; }
            if (dxSellSinAura != null) { dxSellSinAura.Dispose(); dxSellSinAura = null; }
            if (dxSellSinTrack != null) { dxSellSinTrack.Dispose(); dxSellSinTrack = null; }
            if (dxSellSinGhost != null) { dxSellSinGhost.Dispose(); dxSellSinGhost = null; }
            if (dxLabelBg != null) { dxLabelBg.Dispose(); dxLabelBg = null; }
            if (dxTextBrush != null) { dxTextBrush.Dispose(); dxTextBrush = null; }
            if (dxLeaderBrush != null) { dxLeaderBrush.Dispose(); dxLeaderBrush = null; }
            if (dxStrokeDash != null) { dxStrokeDash.Dispose(); dxStrokeDash = null; }
            if (dxStrokeDot != null) { dxStrokeDot.Dispose(); dxStrokeDot = null; }
            if (dxFont != null) { dxFont.Dispose(); dxFont = null; }
            if (dxFactory != null) { dxFactory.Dispose(); dxFactory = null; }
        }

        public override void OnRenderTargetChanged()
        {
            LimparRecursosRender();
        }
    }
}
