#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Media;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
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
        }

        private readonly object syncLock = new object();
        private readonly Dictionary<int, DepthSlot> askSlots = new Dictionary<int, DepthSlot>();
        private readonly Dictionary<int, DepthSlot> bidSlots = new Dictionary<int, DepthSlot>();
        private readonly Dictionary<double, long> askDepthByPrice = new Dictionary<double, long>();
        private readonly Dictionary<double, long> bidDepthByPrice = new Dictionary<double, long>();
        private readonly Dictionary<string, PriceCluster> clusters = new Dictionary<string, PriceCluster>();
        private readonly List<IcebergEvent> events = new List<IcebergEvent>(512);
        private readonly List<IcebergEvent> visibleScratch = new List<IcebergEvent>(128);
        private readonly List<SharpDX.RectangleF> usedLabelRects = new List<SharpDX.RectangleF>(128);

        private double lastBid = 0;
        private double lastAsk = 0;
        private DateTime lastMarketTime = DateTime.MinValue;
        private object speechEngine;
        private Type speechType;
        private bool speechIsManaged;
        private DateTime lastVoiceTime = DateTime.MinValue;

        private SharpDX.DirectWrite.Factory dxFactory;
        private SharpDX.DirectWrite.TextFormat dxFont;
        private SharpDX.Direct2D1.SolidColorBrush dxBuyDinFill, dxBuyDinAura, dxBuyDinBorder;
        private SharpDX.Direct2D1.SolidColorBrush dxSellDinFill, dxSellDinAura, dxSellDinBorder;
        private SharpDX.Direct2D1.SolidColorBrush dxBuySinRing, dxBuySinCenter, dxBuySinAura;
        private SharpDX.Direct2D1.SolidColorBrush dxSellSinRing, dxSellSinCenter, dxSellSinAura;
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
        [Display(Name = "Mostrar Volume Real (Números)", GroupName = "2. Visual e Áudio", Order = 1)]
        public bool MostrarNumeros { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Ativar Alerta de Voz Dinâmico", GroupName = "2. Visual e Áudio", Order = 2)]
        public bool AtivarVoz { get; set; }

        [NinjaScriptProperty]
        [Range(2, 120)]
        [Display(Name = "Janela Iceberg Sintético (seg)", GroupName = "1. Configuração de Lotes", Order = 4)]
        public int JanelaSinteticoSeg { get; set; }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"Rastreador Institucional de Icebergs Dinâmicos (DOM Reload) e Sintéticos (Fracionados)";
                Name = "FluentliWatchdog";
                Calculate = Calculate.OnEachTick;
                IsOverlay = true;
                DrawOnPricePanel = true;
                DisplayInDataBox = false;
                ScaleJustification = NinjaTrader.Gui.Chart.ScaleJustification.Right;

                LotePequeno = 50;
                LoteMedio = 250;
                LoteGigante = 500;
                MostrarNumeros = true;
                AtivarVoz = true;
                JanelaSinteticoSeg = 15;
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

            // Recarregamento passivo no DOM: mesma posição e preço subiu de lote durante agressões (compatível com Live e Market Replay)
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

            lock (syncLock)
            {
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
                int barIdx = CurrentBar;

                if (cl.ActiveEvent != null && cl.ActiveEvent.BarIndex == barIdx)
                {
                    cl.ActiveEvent.Volume = cl.ExecutedVol;
                    cl.ActiveEvent.Timestamp = e.Time;
                    if (detectedKind == IcebergKind.Dinamico) cl.ActiveEvent.Kind = IcebergKind.Dinamico;
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
                        Timestamp = e.Time
                    };
                    events.Add(ev);
                    cl.ActiveEvent = ev;

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

        private void EnsureRenderResources()
        {
            if (dxFactory == null) dxFactory = new SharpDX.DirectWrite.Factory();
            if (dxFont == null) dxFont = new SharpDX.DirectWrite.TextFormat(dxFactory, "Consolas", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 10f);

            // Dinâmico (Preenchido com Halo Neon)
            if (dxBuyDinFill == null) dxBuyDinFill = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.10f, 0.88f, 0.56f, 0.78f));
            if (dxBuyDinAura == null) dxBuyDinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.10f, 0.88f, 0.56f, 0.18f));
            if (dxBuyDinBorder == null) dxBuyDinBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.30f, 1.00f, 0.72f, 0.98f));

            if (dxSellDinFill == null) dxSellDinFill = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.95f, 0.22f, 0.36f, 0.78f));
            if (dxSellDinAura == null) dxSellDinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.95f, 0.22f, 0.36f, 0.18f));
            if (dxSellDinBorder == null) dxSellDinBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1.00f, 0.42f, 0.58f, 0.98f));

            // Sintético (Anel Duplo / Vazado para diferenciar de olho do Dinâmico!)
            if (dxBuySinRing == null) dxBuySinRing = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.16f, 0.94f, 0.84f, 0.98f));
            if (dxBuySinCenter == null) dxBuySinCenter = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.03f, 0.16f, 0.15f, 0.85f));
            if (dxBuySinAura == null) dxBuySinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.16f, 0.94f, 0.84f, 0.16f));

            if (dxSellSinRing == null) dxSellSinRing = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1.00f, 0.54f, 0.16f, 0.98f));
            if (dxSellSinCenter == null) dxSellSinCenter = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.18f, 0.06f, 0.03f, 0.85f));
            if (dxSellSinAura == null) dxSellSinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1.00f, 0.54f, 0.16f, 0.16f));

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

        protected override void OnRender(ChartControl chartControl, ChartScale chartScale)
        {
            if (chartControl == null || chartScale == null || ChartBars == null || ChartPanel == null || RenderTarget == null)
                return;

            visibleScratch.Clear();
            int fromIdx = Math.Max(0, ChartBars.FromIndex);
            int toIdx = ChartBars.ToIndex;

            lock (syncLock)
            {
                for (int i = 0; i < events.Count; i++)
                {
                    IcebergEvent ev = events[i];
                    if (ev.BarIndex >= fromIdx && ev.BarIndex <= toIdx)
                        visibleScratch.Add(ev);
                }
            }

            if (visibleScratch.Count == 0) return;

            EnsureRenderResources();
            usedLabelRects.Clear();
            SharpDX.Direct2D1.AntialiasMode prevAa = RenderTarget.AntialiasMode;
            RenderTarget.AntialiasMode = SharpDX.Direct2D1.AntialiasMode.PerPrimitive;

            float panelLeft = (float)ChartPanel.X;
            float panelTop = (float)ChartPanel.Y;
            float panelRight = (float)(ChartPanel.X + ChartPanel.W);
            float panelBottom = (float)(ChartPanel.Y + ChartPanel.H);

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
                float radius = 5.5f + (float)(Math.Sqrt(norm) * 16.5);
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

            // Passo 2: Desenha todas as etiquetas SEMPRE fora da borda da bolinha (nunca em cima do círculo!)
            for (int i = 0; i < visibleScratch.Count; i++)
            {
                IcebergEvent ev = visibleScratch[i];
                float x = (float)chartControl.GetXByBarIndex(ChartBars, ev.BarIndex);
                float y = (float)chartScale.GetYByValue(ev.Price);
                if (y < panelTop - 20f || y > panelBottom + 20f || x < panelLeft - 20f || x > panelRight + 20f) continue;

                double norm = Math.Max(0.0, Math.Min(1.0, (ev.Volume - minVol) / (maxRef - minVol)));
                float radius = 5.5f + (float)(Math.Sqrt(norm) * 16.5);

                string prefix = (ev.Kind == IcebergKind.Dinamico) ? "D " : "S ";
                string txt = prefix + ev.Volume.ToString();
                float pillW = Math.Max(34f, txt.Length * 6.5f + 10f);
                float pillH = 15f;

                // Posiciona à direita da borda externa da bolinha (ou à esquerda se perto da margem direita)
                float rightCandidateLeft = x + radius + 7f;
                float boxLeft = (rightCandidateLeft + pillW <= panelRight - 4f)
                    ? rightCandidateLeft
                    : Math.Max(panelLeft + 4f, x - radius - pillW - 7f);

                float chosenTop = Math.Max(panelTop + 4f, Math.Min(panelBottom - pillH - 4f, y - pillH * 0.5f));
                if (LabelColide(new SharpDX.RectangleF(boxLeft - 2f, chosenTop - 1f, pillW + 4f, pillH + 2f)))
                {
                    float[] offsets = { -17f, 17f, -34f, 34f, -51f, 51f };
                    foreach (float dy in offsets)
                    {
                        float candTop = Math.Max(panelTop + 4f, Math.Min(panelBottom - pillH - 4f, (y + dy) - pillH * 0.5f));
                        if (!LabelColide(new SharpDX.RectangleF(boxLeft - 2f, candTop - 1f, pillW + 4f, pillH + 2f)))
                        {
                            chosenTop = candTop;
                            break;
                        }
                    }
                }

                SharpDX.RectangleF pillRect = new SharpDX.RectangleF(boxLeft, chosenTop, pillW, pillH);
                usedLabelRects.Add(new SharpDX.RectangleF(boxLeft - 2f, chosenTop - 1f, pillW + 4f, pillH + 2f));

                float edgeX = (boxLeft > x) ? (x + radius + 1f) : (x - radius - 1f);
                float pillEdgeX = (boxLeft > x) ? boxLeft : pillRect.Right;
                RenderTarget.DrawLine(new SharpDX.Vector2(edgeX, y), new SharpDX.Vector2(pillEdgeX, chosenTop + pillH * 0.5f), dxLeaderBrush, 0.85f);

                SharpDX.Direct2D1.SolidColorBrush borderBrush = (ev.Kind == IcebergKind.Dinamico)
                    ? (ev.IsSellSide ? dxSellDinBorder : dxBuyDinBorder)
                    : (ev.IsSellSide ? dxSellSinRing : dxBuySinRing);

                SharpDX.Direct2D1.RoundedRectangle pill = new SharpDX.Direct2D1.RoundedRectangle { Rect = pillRect, RadiusX = 3.5f, RadiusY = 3.5f };
                RenderTarget.FillRoundedRectangle(pill, dxLabelBg);
                RenderTarget.DrawRoundedRectangle(pill, borderBrush, 0.9f);
                RenderTarget.DrawText(txt, dxFont, new SharpDX.RectangleF(boxLeft + 5f, chosenTop + 1.5f, pillW - 6f, pillH - 1f), borderBrush);
            }

            RenderTarget.AntialiasMode = prevAa;
        }

        private void LimparRecursosRender()
        {
            if (dxBuyDinFill != null) { dxBuyDinFill.Dispose(); dxBuyDinFill = null; }
            if (dxBuyDinAura != null) { dxBuyDinAura.Dispose(); dxBuyDinAura = null; }
            if (dxBuyDinBorder != null) { dxBuyDinBorder.Dispose(); dxBuyDinBorder = null; }
            if (dxSellDinFill != null) { dxSellDinFill.Dispose(); dxSellDinFill = null; }
            if (dxSellDinAura != null) { dxSellDinAura.Dispose(); dxSellDinAura = null; }
            if (dxSellDinBorder != null) { dxSellDinBorder.Dispose(); dxSellDinBorder = null; }
            if (dxBuySinRing != null) { dxBuySinRing.Dispose(); dxBuySinRing = null; }
            if (dxBuySinCenter != null) { dxBuySinCenter.Dispose(); dxBuySinCenter = null; }
            if (dxBuySinAura != null) { dxBuySinAura.Dispose(); dxBuySinAura = null; }
            if (dxSellSinRing != null) { dxSellSinRing.Dispose(); dxSellSinRing = null; }
            if (dxSellSinCenter != null) { dxSellSinCenter.Dispose(); dxSellSinCenter = null; }
            if (dxSellSinAura != null) { dxSellSinAura.Dispose(); dxSellSinAura = null; }
            if (dxLabelBg != null) { dxLabelBg.Dispose(); dxLabelBg = null; }
            if (dxTextBrush != null) { dxTextBrush.Dispose(); dxTextBrush = null; }
            if (dxLeaderBrush != null) { dxLeaderBrush.Dispose(); dxLeaderBrush = null; }
            if (dxFont != null) { dxFont.Dispose(); dxFont = null; }
            if (dxFactory != null) { dxFactory.Dispose(); dxFactory = null; }
        }

        public override void OnRenderTargetChanged()
        {
            LimparRecursosRender();
        }
    }
}
