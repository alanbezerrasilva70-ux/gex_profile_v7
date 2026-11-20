#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using Wpf = System.Windows.Controls;
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

public enum VeltrixWatchdogModoVisualV9
{
    LateralNoPreco,
    SobreCandle
}

public enum VeltrixWatchdogPosicaoV9
{
    SuperiorDireito,
    SuperiorEsquerdo,
    InferiorDireito,
    InferiorEsquerdo
}

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
        private readonly List<IcebergEvent> visibleScratch = new List<IcebergEvent>(64);
        private readonly List<IcebergEvent> visibleTrackScratch = new List<IcebergEvent>(32);
        private readonly List<IcebergEvent> recentDynScratch = new List<IcebergEvent>(12);
        private readonly List<IcebergEvent> recentSinScratch = new List<IcebergEvent>(12);
        private readonly List<SharpDX.RectangleF> usedLabelRects = new List<SharpDX.RectangleF>(128);

        private double lastBid = 0;
        private double lastAsk = 0;
        private DateTime lastMarketTime = DateTime.MinValue;
        private object speechEngine;
        private Type speechType;
        private bool speechIsManaged;
        private DateTime lastVoiceTime = DateTime.MinValue;
        private readonly object voiceLock = new object();
        private string lastColorSignature = "";

        private volatile bool pendingUiRefresh = false;
        private long lastInvalidateUtcTicks = 0;
        private int uiInvokeQueued = 0;
        private DispatcherTimer uiRefreshTimer = null;

        private bool mouseHooked = false;
        private bool mouseHookPending = false;
        private bool isDraggingPanel = false;
        private System.Windows.Point dragStartPx;
        private int dragOrigX = 0;
        private int dragOrigY = 0;
        private bool runtimeMinimized = false;
        private bool hasRuntimePosOverride = false;
        private VeltrixWatchdogPosicaoV9 runtimePosOverride = VeltrixWatchdogPosicaoV9.InferiorDireito;
        private SharpDX.RectangleF panelDragRect = new SharpDX.RectangleF(0, 0, 0, 0);
        private SharpDX.RectangleF btnCyclePosRect = new SharpDX.RectangleF(0, 0, 0, 0);
        private SharpDX.RectangleF btnMinimizeRect = new SharpDX.RectangleF(0, 0, 0, 0);

        private Chart attachedOwnerChart = null;
        private Wpf.Button toolbarQuickBtn = null;
        private System.Windows.Window quickSettingsWin = null;
        private DateTime lastToolbarCheckUtc = DateTime.MinValue;
        private bool toolbarAttachPending = false;
        private const string ToolbarBtnTag = "VeltrixToolbar_Watchdog";

        private SharpDX.DirectWrite.Factory dxFactory;
        private SharpDX.DirectWrite.TextFormat dxFont, dxPanelTitleFmt, dxPanelBodyFmt, dxPanelSmallFmt, dxPanelBtnFmt;
        private SharpDX.Direct2D1.StrokeStyle dxStrokeDash, dxStrokeDot;
        private SharpDX.Direct2D1.SolidColorBrush dxBuyDinFill, dxBuyDinAura, dxBuyDinBorder, dxBuyDinTrack, dxBuyDinGhost;
        private SharpDX.Direct2D1.SolidColorBrush dxSellDinFill, dxSellDinAura, dxSellDinBorder, dxSellDinTrack, dxSellDinGhost;
        private SharpDX.Direct2D1.SolidColorBrush dxBuySinRing, dxBuySinCenter, dxBuySinAura, dxBuySinTrack, dxBuySinGhost;
        private SharpDX.Direct2D1.SolidColorBrush dxSellSinRing, dxSellSinCenter, dxSellSinAura, dxSellSinTrack, dxSellSinGhost;
        private SharpDX.Direct2D1.SolidColorBrush dxLabelBg, dxTextBrush, dxLeaderBrush;
        private SharpDX.Direct2D1.SolidColorBrush dxPanelBg, dxPanelBorder, dxPanelDivider, dxMutedBrush, dxBtnBg, dxHighlightRowBg;

        #region Propriedades
        [NinjaScriptProperty]
        [Range(1, 10000)]
        [Display(Name = "1. Lote Minimo Deteccao / Painel", GroupName = "1. Configuração de Lotes", Order = 1)]
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
        [Range(1, 50000)]
        [Display(Name = "5. Filtro Gráfico ES (Só Grandes)", GroupName = "1. Configuração de Lotes", Order = 5)]
        public int LoteMinGraficoES { get; set; }

        [NinjaScriptProperty]
        [Range(1, 50000)]
        [Display(Name = "6. Filtro Gráfico NQ (Só Grandes)", GroupName = "1. Configuração de Lotes", Order = 6)]
        public int LoteMinGraficoNQ { get; set; }

        [NinjaScriptProperty]
        [Range(1, 50000)]
        [Display(Name = "7. Filtro Gráfico Outros Ativos", GroupName = "1. Configuração de Lotes", Order = 7)]
        public int LoteMinGraficoOutros { get; set; }

        [NinjaScriptProperty]
        [Range(0, 50000)]
        [Display(Name = "8. Filtro Manual Gráfico (0=Auto ES/NQ)", GroupName = "1. Configuração de Lotes", Order = 8)]
        public int FiltroGraficoManual { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Modo Visual no Gráfico", GroupName = "2. Visual e Áudio", Order = 1)]
        public VeltrixWatchdogModoVisualV9 ModoVisual { get; set; }

        [NinjaScriptProperty]
        [Range(3, 50)]
        [Display(Name = "Máx. Icebergs Grandes no Gráfico", GroupName = "2. Visual e Áudio", Order = 2)]
        public int MaxIcebergsNoGrafico { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Mostrar Volume Real (Números)", GroupName = "2. Visual e Áudio", Order = 3)]
        public bool MostrarNumeros { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Ativar Alerta de Voz Dinâmico", GroupName = "2. Visual e Áudio", Order = 4)]
        public bool AtivarVoz { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Mostrar Painel Ao Vivo (Din/Sin)", GroupName = "2. Visual e Áudio", Order = 5)]
        public bool MostrarPainelIcebergs { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Posição Painel Icebergs", GroupName = "2. Visual e Áudio", Order = 6)]
        public VeltrixWatchdogPosicaoV9 PosicaoPainel { get; set; }

        [NinjaScriptProperty]
        [Range(0, 100)]
        [Display(Name = "Opacidade Fundo Painel (%)", GroupName = "2. Visual e Áudio", Order = 7)]
        public int OpacidadePainelPct { get; set; }

        [NinjaScriptProperty]
        [Range(-2000, 2000)]
        [Display(Name = "Ajuste Painel X (px)", GroupName = "2. Visual e Áudio", Order = 8)]
        public int OffsetPainelX { get; set; }

        [NinjaScriptProperty]
        [Range(-2000, 2000)]
        [Display(Name = "Ajuste Painel Y (px)", GroupName = "2. Visual e Áudio", Order = 9)]
        public int OffsetPainelY { get; set; }

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
        [XmlIgnore]
        [Display(Name = "5. Cor Fundo Painel", GroupName = "3. Cores Personalizadas", Order = 5)]
        public System.Windows.Media.Brush CorFundoPainel { get; set; }

        [Browsable(false)]
        public string CorFundoPainelSerialize
        {
            get { return Serialize.BrushToString(CorFundoPainel ?? System.Windows.Media.Brushes.Black); }
            set { if (!string.IsNullOrEmpty(value)) CorFundoPainel = Serialize.StringToBrush(value); }
        }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "6. Cor Borda Painel", GroupName = "3. Cores Personalizadas", Order = 6)]
        public System.Windows.Media.Brush CorBordaPainel { get; set; }

        [Browsable(false)]
        public string CorBordaPainelSerialize
        {
            get { return Serialize.BrushToString(CorBordaPainel ?? System.Windows.Media.Brushes.SteelBlue); }
            set { if (!string.IsNullOrEmpty(value)) CorBordaPainel = Serialize.StringToBrush(value); }
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
        #endregion

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"Rastreador Institucional de Icebergs Dinâmicos e Sintéticos com Filtro por Ativo (ES 800 / NQ 200), Linha Lateral Limpa e Painel Ao Vivo.";
                Name = "VeltrixQuant - FluentliWatchdog";
                Calculate = Calculate.OnEachTick;
                IsOverlay = true;
                DrawOnPricePanel = true;
                DisplayInDataBox = false;
                ScaleJustification = NinjaTrader.Gui.Chart.ScaleJustification.Right;

                LotePequeno = 50;
                LoteMedio = 250;
                LoteGigante = 500;
                JanelaSinteticoSeg = 15;
                LoteMinGraficoES = 800;
                LoteMinGraficoNQ = 200;
                LoteMinGraficoOutros = 100;
                FiltroGraficoManual = 0;

                ModoVisual = VeltrixWatchdogModoVisualV9.LateralNoPreco;
                MaxIcebergsNoGrafico = 18;
                MostrarNumeros = true;
                AtivarVoz = true;
                MostrarPainelIcebergs = true;
                PosicaoPainel = VeltrixWatchdogPosicaoV9.InferiorDireito;
                OpacidadePainelPct = 88;
                OffsetPainelX = 0;
                OffsetPainelY = 0;

                CorCompraDinamico = System.Windows.Media.Brushes.MediumSpringGreen;
                CorVendaDinamico = System.Windows.Media.Brushes.Crimson;
                CorCompraSintetico = System.Windows.Media.Brushes.Cyan;
                CorVendaSintetico = System.Windows.Media.Brushes.DarkOrange;

                var bgB = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(12, 16, 27));
                bgB.Freeze();
                CorFundoPainel = bgB;
                var bdB = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(56, 76, 112));
                bdB.Freeze();
                CorBordaPainel = bdB;

                AtivarLinhaRastreio = true;
                RastreioLoteMinimo = 200;
                ToleranciaRastreioTicks = 8;
                MaxLinhasRastreio = 6;
            }
            else if (State == State.DataLoaded)
            {
                InitSpeech();
                EnsureMouseHooked();
            }
            else if (State == State.Terminated)
            {
                RemoveToolbarButton();
                UnhookMouseEvents();
                LimparRecursosRender();
                DisposeSpeech();
            }
        }

        private int ResolveChartPlotThreshold()
        {
            if (FiltroGraficoManual > 0)
                return FiltroGraficoManual;
            string sym = (Instrument != null && Instrument.MasterInstrument != null)
                ? (Instrument.MasterInstrument.Name ?? string.Empty).Trim().ToUpperInvariant()
                : string.Empty;
            if (sym == "ES" || sym == "$SPX" || sym == "SPY")
                return Math.Max(1, LoteMinGraficoES);
            if (sym == "NQ" || sym == "$NDX" || sym == "QQQ")
                return Math.Max(1, LoteMinGraficoNQ);
            return Math.Max(1, LoteMinGraficoOutros);
        }

        private VeltrixWatchdogPosicaoV9 GetEffectivePos()
        {
            return hasRuntimePosOverride ? runtimePosOverride : PosicaoPainel;
        }

        private void RequestInstantChartRefresh()
        {
            pendingUiRefresh = true;
            if (State == State.Terminated || ChartControl == null) return;

            long nowTicks = DateTime.UtcNow.Ticks;
            long prevTicks = Interlocked.Read(ref lastInvalidateUtcTicks);
            if ((nowTicks - prevTicks) < TimeSpan.TicksPerMillisecond * 45)
                return;

            if (Interlocked.CompareExchange(ref uiInvokeQueued, 1, 0) != 0)
                return;

            Interlocked.Exchange(ref lastInvalidateUtcTicks, nowTicks);
            try
            {
                ChartControl.Dispatcher.BeginInvoke(DispatcherPriority.Render, new Action(() =>
                {
                    try
                    {
                        Interlocked.Exchange(ref uiInvokeQueued, 0);
                        pendingUiRefresh = false;
                        if (State != State.Terminated && ChartControl != null)
                            ChartControl.InvalidateVisual();
                    }
                    catch
                    {
                        Interlocked.Exchange(ref uiInvokeQueued, 0);
                    }
                }));
            }
            catch
            {
                Interlocked.Exchange(ref uiInvokeQueued, 0);
            }
        }

        private void OnUiRefreshTimerTick(object sender, EventArgs e)
        {
            if (State == State.Terminated || ChartControl == null) return;
            if (pendingUiRefresh)
            {
                pendingUiRefresh = false;
                ChartControl.InvalidateVisual();
            }
        }

        private void EnsureMouseHooked()
        {
            EnsureToolbarAttachedThrottled();
            if (mouseHooked || mouseHookPending || ChartControl == null) return;
            mouseHookPending = true;
            try
            {
                ChartControl.Dispatcher.InvokeAsync(new Action(() =>
                {
                    mouseHookPending = false;
                    if (State == State.Terminated || ChartControl == null || mouseHooked) return;
                    ChartControl.PreviewMouseLeftButtonDown += OnChartPreviewMouseLeftButtonDown;
                    ChartControl.PreviewMouseMove += OnChartPreviewMouseMove;
                    ChartControl.PreviewMouseLeftButtonUp += OnChartPreviewMouseLeftButtonUp;
                    ChartControl.LostMouseCapture += OnChartLostMouseCapture;
                    if (uiRefreshTimer == null)
                    {
                        uiRefreshTimer = new DispatcherTimer(DispatcherPriority.Render, ChartControl.Dispatcher);
                        uiRefreshTimer.Interval = TimeSpan.FromMilliseconds(100);
                        uiRefreshTimer.Tick += OnUiRefreshTimerTick;
                        uiRefreshTimer.Start();
                    }
                    mouseHooked = true;
                }));
            }
            catch
            {
                mouseHookPending = false;
            }
        }

        private void UnhookMouseEvents()
        {
            if (ChartControl == null) return;
            try
            {
                ChartControl.Dispatcher.InvokeAsync(new Action(() =>
                {
                    if (uiRefreshTimer != null)
                    {
                        try
                        {
                            uiRefreshTimer.Stop();
                            uiRefreshTimer.Tick -= OnUiRefreshTimerTick;
                        }
                        catch { }
                        uiRefreshTimer = null;
                    }
                    if (ChartControl != null && mouseHooked)
                    {
                        ChartControl.PreviewMouseLeftButtonDown -= OnChartPreviewMouseLeftButtonDown;
                        ChartControl.PreviewMouseMove -= OnChartPreviewMouseMove;
                        ChartControl.PreviewMouseLeftButtonUp -= OnChartPreviewMouseLeftButtonUp;
                        ChartControl.LostMouseCapture -= OnChartLostMouseCapture;
                        mouseHooked = false;
                    }
                }));
            }
            catch { }
        }

        private void OnChartPreviewMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.Handled || !MostrarPainelIcebergs || ChartControl == null || ChartControl.PresentationSource == null) return;

            System.Windows.Point p = e.GetPosition(ChartControl);
            float px = (float)ChartingExtensions.ConvertToHorizontalPixels(p.X, ChartControl.PresentationSource);
            float py = (float)ChartingExtensions.ConvertToVerticalPixels(p.Y, ChartControl.PresentationSource);

            if (btnMinimizeRect.Width > 0 && btnMinimizeRect.Contains(px, py))
            {
                runtimeMinimized = !runtimeMinimized;
                e.Handled = true;
                ChartControl.InvalidateVisual();
                return;
            }

            if (btnCyclePosRect.Width > 0 && btnCyclePosRect.Contains(px, py))
            {
                VeltrixWatchdogPosicaoV9 cur = GetEffectivePos();
                VeltrixWatchdogPosicaoV9 next;
                switch (cur)
                {
                    case VeltrixWatchdogPosicaoV9.InferiorDireito: next = VeltrixWatchdogPosicaoV9.InferiorEsquerdo; break;
                    case VeltrixWatchdogPosicaoV9.InferiorEsquerdo: next = VeltrixWatchdogPosicaoV9.SuperiorEsquerdo; break;
                    case VeltrixWatchdogPosicaoV9.SuperiorEsquerdo: next = VeltrixWatchdogPosicaoV9.SuperiorDireito; break;
                    default: next = VeltrixWatchdogPosicaoV9.InferiorDireito; break;
                }
                runtimePosOverride = next;
                hasRuntimePosOverride = true;
                PosicaoPainel = next;
                OffsetPainelX = 0;
                OffsetPainelY = 0;
                e.Handled = true;
                ChartControl.InvalidateVisual();
                return;
            }

            if (panelDragRect.Width > 0 && panelDragRect.Contains(px, py))
            {
                isDraggingPanel = true;
                dragStartPx = new System.Windows.Point(px, py);
                dragOrigX = OffsetPainelX;
                dragOrigY = OffsetPainelY;
                ChartControl.CaptureMouse();
                e.Handled = true;
            }
        }

        private void OnChartPreviewMouseMove(object sender, MouseEventArgs e)
        {
            if (!isDraggingPanel || ChartControl == null || ChartControl.PresentationSource == null) return;
            System.Windows.Point p = e.GetPosition(ChartControl);
            float px = (float)ChartingExtensions.ConvertToHorizontalPixels(p.X, ChartControl.PresentationSource);
            float py = (float)ChartingExtensions.ConvertToVerticalPixels(p.Y, ChartControl.PresentationSource);

            OffsetPainelX = Math.Max(-2000, Math.Min(2000, dragOrigX + (int)Math.Round(px - dragStartPx.X)));
            OffsetPainelY = Math.Max(-2000, Math.Min(2000, dragOrigY + (int)Math.Round(py - dragStartPx.Y)));
            ChartControl.InvalidateVisual();
        }

        private void OnChartPreviewMouseLeftButtonUp(object sender, MouseButtonEventArgs e)
        {
            if (!isDraggingPanel) return;
            isDraggingPanel = false;
            if (ChartControl != null && ChartControl.IsMouseCaptured)
                ChartControl.ReleaseMouseCapture();
            e.Handled = true;
        }

        private void OnChartLostMouseCapture(object sender, MouseEventArgs e)
        {
            isDraggingPanel = false;
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
                    try { t.InvokeMember("Rate", BindingFlags.SetProperty, null, eng, new object[] { 2 }); } catch { }
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
                    try { comType.InvokeMember("Rate", BindingFlags.SetProperty, null, comVoice, new object[] { 2 }); } catch { }
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
                {
                    try { speechType.InvokeMember("SpeakAsyncCancelAll", BindingFlags.InvokeMethod, null, speechEngine, null); } catch { }
                    speechType.InvokeMember("SpeakAsync", BindingFlags.InvokeMethod, null, speechEngine, new object[] { msg });
                }
                else
                {
                    speechType.InvokeMember("Speak", BindingFlags.InvokeMethod, null, speechEngine, new object[] { msg, 3 });
                }
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
            if (pendingUiRefresh && State == State.Realtime)
                RequestInstantChartRefresh();
        }

        private double GetTolerancePrice()
        {
            double tickSz = (TickSize > 0) ? TickSize : 0.25;
            int ticks = (ToleranciaRastreioTicks >= 1) ? ToleranciaRastreioTicks : 8;
            return ticks * tickSz;
        }

        private bool AtualizarLinhasRastreio(double preco, int barIdx)
        {
            if (!AtivarLinhaRastreio) return false;
            bool changed = false;
            double tol = GetTolerancePrice();
            for (int i = 0; i < events.Count; i++)
            {
                IcebergEvent ev = events[i];
                if (!ev.TrackActive) continue;

                bool rompeu = ev.IsSellSide
                    ? (preco > ev.Price + tol)
                    : (preco < ev.Price - tol);

                if (ev.TrackEndBarIndex < barIdx)
                {
                    ev.TrackEndBarIndex = barIdx;
                    changed = true;
                }
                if (rompeu)
                {
                    ev.TrackActive = false;
                    ev.TrackCompleted = true;
                    changed = true;
                }
            }
            return changed;
        }

        private long GetVisibleDepthSafe(Dictionary<double, long> depthMap, double preco)
        {
            long val;
            if (depthMap.TryGetValue(preco, out val))
                return val;
            double tickTol = ((TickSize > 0) ? TickSize : 0.25) * 0.25;
            foreach (var kv in depthMap)
            {
                if (Math.Abs(kv.Key - preco) <= tickTol)
                    return kv.Value;
            }
            return 0;
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

            if (e.Operation == NinjaTrader.Cbi.Operation.Update && hadPrev && Math.Abs(oldPrice - e.Price) < 1e-9 && e.Volume > oldVol)
            {
                string key = (isSellSide ? "S_" : "B_") + e.Price.ToString("G17", CultureInfo.InvariantCulture);
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
            bool uiDirtyNeeded = false;
            int barIdx = CurrentBar;

            lock (syncLock)
            {
                if (AtualizarLinhasRastreio(preco, barIdx))
                    uiDirtyNeeded = true;

                string key = (icebergDeVenda ? "S_" : "B_") + preco.ToString("G17", CultureInfo.InvariantCulture);
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
                long visibleDepth = hasDepthData ? GetVisibleDepthSafe(depthMap, preco) : 0;

                bool isDinamico =
                    (cl.ReloadCount >= 2 && cl.ExecutedVol >= LotePequeno) ||
                    (hasDepthData && agressao >= LotePequeno && agressao > visibleDepth) ||
                    (!hasDepthData && agressao >= LotePequeno);

                bool isSintetico = !isDinamico && cl.TradeCount >= 2 && cl.ExecutedVol >= LotePequeno;

                if (isDinamico || isSintetico)
                {
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

                    uiDirtyNeeded = true;

                    int tier = (cl.ExecutedVol >= LoteGigante) ? 3 : ((cl.ExecutedVol >= LoteMedio) ? 2 : 1);
                    if (tier > cl.SpokenTier)
                    {
                        cl.SpokenTier = tier;
                        string tipoTxt = (cl.ActiveEvent.Kind == IcebergKind.Dinamico) ? "Dinâmico" : "Sintético";
                        string ladoTxt = icebergDeVenda ? "Venda" : "Compra";
                        if (tier == 3) voiceMsg = "Iceberg " + tipoTxt + " Gigante " + ladoTxt;
                        else if (tier == 2) voiceMsg = "Iceberg " + tipoTxt + " Médio " + ladoTxt;
                        else voiceMsg = "Iceberg " + tipoTxt + " " + ladoTxt;
                    }
                }
            }

            if (State == State.Realtime)
            {
                if (uiDirtyNeeded)
                    RequestInstantChartRefresh();

                if (voiceMsg != null && AtivarVoz)
                {
                    bool shouldSpeak = false;
                    lock (voiceLock)
                    {
                        if ((DateTime.UtcNow - lastVoiceTime).TotalSeconds >= 1.4)
                        {
                            lastVoiceTime = DateTime.UtcNow;
                            shouldSpeak = true;
                        }
                    }
                    if (shouldSpeak)
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
            int safeAlpha = Math.Max(0, Math.Min(100, OpacidadePainelPct));
            string sig = ColorKeyPart(CorCompraDinamico) + "|" + ColorKeyPart(CorVendaDinamico)
                + "|" + ColorKeyPart(CorCompraSintetico) + "|" + ColorKeyPart(CorVendaSintetico)
                + "|" + ColorKeyPart(CorFundoPainel) + "|" + ColorKeyPart(CorBordaPainel) + "|" + safeAlpha;
            if (!string.IsNullOrEmpty(lastColorSignature) && lastColorSignature != sig)
            {
                LimparRecursosRender();
            }
            lastColorSignature = sig;

            if (dxFactory == null) dxFactory = new SharpDX.DirectWrite.Factory();
            if (dxFont == null) dxFont = new SharpDX.DirectWrite.TextFormat(dxFactory, "Consolas", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 10f);
            if (dxPanelTitleFmt == null) dxPanelTitleFmt = new SharpDX.DirectWrite.TextFormat(dxFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 10.2f);
            if (dxPanelBodyFmt == null) dxPanelBodyFmt = new SharpDX.DirectWrite.TextFormat(dxFactory, "Consolas", SharpDX.DirectWrite.FontWeight.SemiBold, SharpDX.DirectWrite.FontStyle.Normal, 9.6f);
            if (dxPanelSmallFmt == null) dxPanelSmallFmt = new SharpDX.DirectWrite.TextFormat(dxFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Normal, SharpDX.DirectWrite.FontStyle.Normal, 9.0f);
            if (dxPanelBtnFmt == null)
            {
                dxPanelBtnFmt = new SharpDX.DirectWrite.TextFormat(dxFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 9.5f);
                dxPanelBtnFmt.TextAlignment = SharpDX.DirectWrite.TextAlignment.Center;
                dxPanelBtnFmt.ParagraphAlignment = SharpDX.DirectWrite.ParagraphAlignment.Center;
            }

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

            if (dxBuyDinFill == null) dxBuyDinFill = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuyDin.Red, cBuyDin.Green, cBuyDin.Blue, 0.80f));
            if (dxBuyDinAura == null) dxBuyDinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuyDin.Red, cBuyDin.Green, cBuyDin.Blue, 0.20f));
            if (dxBuyDinBorder == null) dxBuyDinBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, LightenColor4(cBuyDin, 0.18f, 0.98f));
            if (dxBuyDinTrack == null) dxBuyDinTrack = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuyDin.Red, cBuyDin.Green, cBuyDin.Blue, 0.84f));
            if (dxBuyDinGhost == null) dxBuyDinGhost = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuyDin.Red, cBuyDin.Green, cBuyDin.Blue, 0.36f));

            if (dxSellDinFill == null) dxSellDinFill = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellDin.Red, cSellDin.Green, cSellDin.Blue, 0.80f));
            if (dxSellDinAura == null) dxSellDinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellDin.Red, cSellDin.Green, cSellDin.Blue, 0.20f));
            if (dxSellDinBorder == null) dxSellDinBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, LightenColor4(cSellDin, 0.18f, 0.98f));
            if (dxSellDinTrack == null) dxSellDinTrack = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellDin.Red, cSellDin.Green, cSellDin.Blue, 0.84f));
            if (dxSellDinGhost == null) dxSellDinGhost = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellDin.Red, cSellDin.Green, cSellDin.Blue, 0.36f));

            if (dxBuySinRing == null) dxBuySinRing = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red, cBuySin.Green, cBuySin.Blue, 0.98f));
            if (dxBuySinCenter == null) dxBuySinCenter = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red * 0.15f, cBuySin.Green * 0.18f, cBuySin.Blue * 0.18f, 0.88f));
            if (dxBuySinAura == null) dxBuySinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red, cBuySin.Green, cBuySin.Blue, 0.18f));
            if (dxBuySinTrack == null) dxBuySinTrack = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red, cBuySin.Green, cBuySin.Blue, 0.84f));
            if (dxBuySinGhost == null) dxBuySinGhost = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cBuySin.Red, cBuySin.Green, cBuySin.Blue, 0.36f));

            if (dxSellSinRing == null) dxSellSinRing = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red, cSellSin.Green, cSellSin.Blue, 0.98f));
            if (dxSellSinCenter == null) dxSellSinCenter = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red * 0.18f, cSellSin.Green * 0.12f, cSellSin.Blue * 0.10f, 0.88f));
            if (dxSellSinAura == null) dxSellSinAura = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red, cSellSin.Green, cSellSin.Blue, 0.18f));
            if (dxSellSinTrack == null) dxSellSinTrack = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red, cSellSin.Green, cSellSin.Blue, 0.84f));
            if (dxSellSinGhost == null) dxSellSinGhost = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(cSellSin.Red, cSellSin.Green, cSellSin.Blue, 0.36f));

            if (dxLabelBg == null) dxLabelBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.03f, 0.05f, 0.09f, 0.92f));
            if (dxTextBrush == null) dxTextBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.95f, 0.97f, 1.00f, 1.00f));
            if (dxLeaderBrush == null) dxLeaderBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.70f, 0.78f, 0.90f, 0.58f));

            float bgA = safeAlpha / 100.0f;
            if (dxPanelBg == null) dxPanelBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, ExtractColor4(CorFundoPainel, new Color4(0.05f, 0.06f, 0.11f, bgA), bgA));
            if (dxPanelBorder == null) dxPanelBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, ExtractColor4(CorBordaPainel, new Color4(0.22f, 0.30f, 0.44f, 0.92f), 0.92f));
            if (dxPanelDivider == null) dxPanelDivider = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.70f, 0.80f, 0.95f, 0.16f));
            if (dxMutedBrush == null) dxMutedBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.65f, 0.72f, 0.84f, 0.92f));
            if (dxBtnBg == null) dxBtnBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1.0f, 1.0f, 1.0f, 0.10f));
            if (dxHighlightRowBg == null) dxHighlightRowBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1.0f, 1.0f, 1.0f, 0.07f));
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

            float[] offsets = { -17f, 17f, -34f, 34f, -51f, 51f, -68f, 68f };
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

        private string FormatPriceSafe(double price)
        {
            try
            {
                if (Instrument != null && Instrument.MasterInstrument != null)
                    return Instrument.MasterInstrument.FormatPrice(price);
            }
            catch { }
            return price.ToString("0.00", CultureInfo.InvariantCulture);
        }

        private void DrawIcebergMarkerShape(IcebergEvent ev, float x, float y, double minVol, double maxRef)
        {
            double norm = Math.Max(0.0, Math.Min(1.0, (ev.Volume - minVol) / Math.Max(10.0, maxRef - minVol)));
            float radius = 6.0f + (float)(Math.Sqrt(norm) * 14.0);
            SharpDX.Vector2 center = new SharpDX.Vector2(x, y);

            if (ev.Kind == IcebergKind.Dinamico)
            {
                RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(center, radius + 4.0f, radius + 4.0f), ev.IsSellSide ? dxSellDinAura : dxBuyDinAura);
                RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(center, radius, radius), ev.IsSellSide ? dxSellDinFill : dxBuyDinFill);
                RenderTarget.DrawEllipse(new SharpDX.Direct2D1.Ellipse(center, radius, radius), ev.IsSellSide ? dxSellDinBorder : dxBuyDinBorder, 1.4f);
            }
            else
            {
                RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(center, radius + 3.5f, radius + 3.5f), ev.IsSellSide ? dxSellSinAura : dxBuySinAura);
                RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(center, radius, radius), ev.IsSellSide ? dxSellSinCenter : dxBuySinCenter);
                RenderTarget.DrawEllipse(new SharpDX.Direct2D1.Ellipse(center, radius, radius), ev.IsSellSide ? dxSellSinRing : dxBuySinRing, 2.2f);
                if (radius >= 7.5f)
                    RenderTarget.DrawEllipse(new SharpDX.Direct2D1.Ellipse(center, radius * 0.50f, radius * 0.50f), ev.IsSellSide ? dxSellSinRing : dxBuySinRing, 1.1f);
            }
        }

        private string FormatBarsPeriodTag()
        {
            try
            {
                if (BarsPeriod != null)
                {
                    string unit = string.Empty;
                    switch (BarsPeriod.BarsPeriodType)
                    {
                        case BarsPeriodType.Minute: unit = "m"; break;
                        case BarsPeriodType.Second: unit = "s"; break;
                        case BarsPeriodType.Range: unit = "R"; break;
                        case BarsPeriodType.Tick: unit = "T"; break;
                        case BarsPeriodType.Volume: unit = "V"; break;
                        default: unit = BarsPeriod.BarsPeriodType.ToString(); break;
                    }
                    return "[" + BarsPeriod.Value + unit + "]";
                }
            }
            catch { }
            return string.Empty;
        }

        private void RenderLiveIcebergsPanel(float panelLeft, float panelTop, float panelRight, float panelBottom, int chartMinVol, int totalDynCount, int totalSinCount)
        {
            if (!MostrarPainelIcebergs)
            {
                panelDragRect = new SharpDX.RectangleF(0, 0, 0, 0);
                btnCyclePosRect = new SharpDX.RectangleF(0, 0, 0, 0);
                btnMinimizeRect = new SharpDX.RectangleF(0, 0, 0, 0);
                return;
            }

            string instName = (Instrument != null && Instrument.MasterInstrument != null) ? Instrument.MasterInstrument.Name : "ATIVO";
            string tfTag = FormatBarsPeriodTag();
            string instLabel = string.IsNullOrEmpty(tfTag) ? instName : (instName + " " + tfTag);
            bool isMin = runtimeMinimized;
            float cardW = isMin ? 368f : 444f;
            float cardH = isMin ? 26f : 158f;
            VeltrixWatchdogPosicaoV9 pos = GetEffectivePos();

            float baseLeft = (pos == VeltrixWatchdogPosicaoV9.SuperiorEsquerdo || pos == VeltrixWatchdogPosicaoV9.InferiorEsquerdo)
                ? (panelLeft + 10f)
                : (panelRight - cardW - 12f);
            float baseTop = (pos == VeltrixWatchdogPosicaoV9.InferiorEsquerdo || pos == VeltrixWatchdogPosicaoV9.InferiorDireito)
                ? (panelBottom - cardH - 12f)
                : (panelTop + 10f);

            float cardLeft = Math.Max(panelLeft + 4f, Math.Min(panelRight - cardW - 4f, baseLeft + OffsetPainelX));
            float cardTop = Math.Max(panelTop + 4f, Math.Min(panelBottom - cardH - 4f, baseTop + OffsetPainelY));

            SharpDX.RectangleF cardRect = new SharpDX.RectangleF(cardLeft, cardTop, cardW, cardH);
            btnMinimizeRect = new SharpDX.RectangleF(cardLeft + cardW - 22f, cardTop + 4.5f, 16f, 16f);
            btnCyclePosRect = new SharpDX.RectangleF(btnMinimizeRect.Left - 20f, cardTop + 4.5f, 16f, 16f);
            panelDragRect = new SharpDX.RectangleF(cardLeft, cardTop, btnCyclePosRect.Left - cardLeft - 4f, 24f);

            SharpDX.Direct2D1.RoundedRectangle rrCard = new SharpDX.Direct2D1.RoundedRectangle { Rect = cardRect, RadiusX = 6f, RadiusY = 6f };
            RenderTarget.FillRoundedRectangle(rrCard, dxPanelBg);
            RenderTarget.DrawRoundedRectangle(rrCard, dxPanelBorder, 1.0f);

            SharpDX.Direct2D1.RoundedRectangle rrPos = new SharpDX.Direct2D1.RoundedRectangle { Rect = btnCyclePosRect, RadiusX = 3f, RadiusY = 3f };
            RenderTarget.FillRoundedRectangle(rrPos, dxBtnBg);
            RenderTarget.DrawRoundedRectangle(rrPos, dxPanelBorder, 0.7f);
            RenderTarget.DrawText("⇄", dxPanelBtnFmt, btnCyclePosRect, dxTextBrush);

            SharpDX.Direct2D1.RoundedRectangle rrMin = new SharpDX.Direct2D1.RoundedRectangle { Rect = btnMinimizeRect, RadiusX = 3f, RadiusY = 3f };
            RenderTarget.FillRoundedRectangle(rrMin, dxBtnBg);
            RenderTarget.DrawRoundedRectangle(rrMin, dxPanelBorder, 0.7f);
            RenderTarget.DrawText(isMin ? "+" : "−", dxPanelBtnFmt, btnMinimizeRect, dxTextBrush);

            if (isMin)
            {
                string minTxt = "❄ ICEBERGS · " + instLabel + " (GRAF≥" + chartMinVol + ") · D:" + totalDynCount + " S:" + totalSinCount;
                RenderTarget.DrawText(minTxt, dxPanelTitleFmt, new SharpDX.RectangleF(cardLeft + 8f, cardTop + 5f, btnCyclePosRect.Left - cardLeft - 12f, 16f), dxTextBrush);
                return;
            }

            string hdrTxt = "❄ ICEBERGS AO VIVO · " + instLabel + "  (PAINEL≥" + LotePequeno + " | GRAF≥" + chartMinVol + ")";
            RenderTarget.DrawText(hdrTxt, dxPanelTitleFmt, new SharpDX.RectangleF(cardLeft + 10f, cardTop + 5.5f, btnCyclePosRect.Left - cardLeft - 14f, 16f), dxTextBrush);

            float sepY = cardTop + 25f;
            RenderTarget.DrawLine(new SharpDX.Vector2(cardLeft + 8f, sepY), new SharpDX.Vector2(cardLeft + cardW - 8f, sepY), dxPanelDivider, 0.9f);

            float colW = (cardW - 22f) * 0.5f;
            float leftColX = cardLeft + 9f;
            float rightColX = leftColX + colW + 6f;
            float midX = leftColX + colW + 2f;
            RenderTarget.DrawLine(new SharpDX.Vector2(midX, sepY + 4f), new SharpDX.Vector2(midX, cardTop + cardH - 20f), dxPanelDivider, 0.8f);

            RenderTarget.DrawText("DINÂMICOS (DOM) · " + totalDynCount, dxPanelSmallFmt, new SharpDX.RectangleF(leftColX, sepY + 3f, colW, 13f), dxBuyDinBorder);
            RenderTarget.DrawText("SINTÉTICOS (FAT) · " + totalSinCount, dxPanelSmallFmt, new SharpDX.RectangleF(rightColX, sepY + 3f, colW, 13f), dxBuySinRing);

            float rowY = sepY + 18f;
            int maxRows = 6;
            for (int r = 0; r < maxRows; r++)
            {
                if (r < recentDynScratch.Count)
                {
                    IcebergEvent dEv = recentDynScratch[r];
                    bool isBig = dEv.Volume >= chartMinVol;
                    if (isBig)
                        RenderTarget.FillRectangle(new SharpDX.RectangleF(leftColX - 2f, rowY - 1f, colW, 14f), dxHighlightRowBg);
                    string tmStr = (dEv.Timestamp != DateTime.MinValue) ? dEv.Timestamp.ToString("HH:mm:ss", CultureInfo.InvariantCulture) + " " : string.Empty;
                    string line = tmStr + (isBig ? "★" : "·") + (dEv.IsSellSide ? "V " : "C ") + dEv.Volume + " @ " + FormatPriceSafe(dEv.Price);
                    var br = dEv.IsSellSide ? dxSellDinBorder : dxBuyDinBorder;
                    RenderTarget.DrawText(line, dxPanelBodyFmt, new SharpDX.RectangleF(leftColX, rowY, colW - 2f, 13f), br);
                }
                else if (r == 0 && recentDynScratch.Count == 0)
                {
                    RenderTarget.DrawText("Aguardando...", dxPanelSmallFmt, new SharpDX.RectangleF(leftColX, rowY, colW, 13f), dxMutedBrush);
                }

                if (r < recentSinScratch.Count)
                {
                    IcebergEvent sEv = recentSinScratch[r];
                    bool isBig = sEv.Volume >= chartMinVol;
                    if (isBig)
                        RenderTarget.FillRectangle(new SharpDX.RectangleF(rightColX - 2f, rowY - 1f, colW, 14f), dxHighlightRowBg);
                    string tmStr = (sEv.Timestamp != DateTime.MinValue) ? sEv.Timestamp.ToString("HH:mm:ss", CultureInfo.InvariantCulture) + " " : string.Empty;
                    string line = tmStr + (isBig ? "★" : "·") + (sEv.IsSellSide ? "V " : "C ") + sEv.Volume + " @ " + FormatPriceSafe(sEv.Price);
                    var br = sEv.IsSellSide ? dxSellSinRing : dxBuySinRing;
                    RenderTarget.DrawText(line, dxPanelBodyFmt, new SharpDX.RectangleF(rightColX, rowY, colW - 2f, 13f), br);
                }
                else if (r == 0 && recentSinScratch.Count == 0)
                {
                    RenderTarget.DrawText("Aguardando...", dxPanelSmallFmt, new SharpDX.RectangleF(rightColX, rowY, colW, 13f), dxMutedBrush);
                }

                rowY += 15.5f;
            }

            string foot = "★ No Gráfico (≥" + chartMinVol + ") | Modo: " + (ModoVisual == VeltrixWatchdogModoVisualV9.LateralNoPreco ? "Linha Lateral" : "Candle");
            RenderTarget.DrawText(foot, dxPanelSmallFmt, new SharpDX.RectangleF(cardLeft + 9f, cardTop + cardH - 17f, cardW - 18f, 14f), dxMutedBrush);
        }

        protected override void OnRender(ChartControl chartControl, ChartScale chartScale)
        {
            if (chartControl == null || chartScale == null || ChartBars == null || ChartPanel == null || RenderTarget == null)
                return;

            EnsureMouseHooked();
            EnsureRenderResources();

            int chartMinVol = ResolveChartPlotThreshold();
            int maxOnChart = Math.Max(3, MaxIcebergsNoGrafico);
            visibleScratch.Clear();
            visibleTrackScratch.Clear();
            recentDynScratch.Clear();
            recentSinScratch.Clear();

            int fromIdx = Math.Max(0, ChartBars.FromIndex);
            int toIdx = ChartBars.ToIndex;
            int totalDynCount = 0;
            int totalSinCount = 0;

            lock (syncLock)
            {
                for (int i = events.Count - 1; i >= 0; i--)
                {
                    IcebergEvent ev = events[i];
                    if (ev.Kind == IcebergKind.Dinamico)
                    {
                        totalDynCount++;
                        if (recentDynScratch.Count < 6) recentDynScratch.Add(ev);
                    }
                    else
                    {
                        totalSinCount++;
                        if (recentSinScratch.Count < 6) recentSinScratch.Add(ev);
                    }

                    if (ev.Volume >= chartMinVol && ev.BarIndex >= fromIdx && ev.BarIndex <= toIdx)
                    {
                        if (ModoVisual == VeltrixWatchdogModoVisualV9.SobreCandle || visibleScratch.Count < maxOnChart)
                            visibleScratch.Add(ev);
                    }

                    if (AtivarLinhaRastreio && (ev.TrackActive || ev.TrackCompleted) && ev.Volume >= chartMinVol)
                    {
                        int endIdx = ev.TrackActive ? Math.Max(ev.TrackEndBarIndex, toIdx) : ev.TrackEndBarIndex;
                        if (endIdx >= fromIdx && ev.BarIndex <= toIdx)
                            visibleTrackScratch.Add(ev);
                    }
                }
            }

            visibleScratch.Reverse();
            visibleTrackScratch.Reverse();
            usedLabelRects.Clear();

            SharpDX.Direct2D1.AntialiasMode prevAa = RenderTarget.AntialiasMode;
            RenderTarget.AntialiasMode = SharpDX.Direct2D1.AntialiasMode.PerPrimitive;

            float panelLeft = (float)ChartPanel.X;
            float panelTop = (float)ChartPanel.Y;
            float panelRight = (float)(ChartPanel.X + ChartPanel.W);
            float panelBottom = (float)(ChartPanel.Y + ChartPanel.H);
            float rightAnchorX = (toIdx >= fromIdx)
                ? Math.Min(panelRight - 130f, (float)chartControl.GetXByBarIndex(ChartBars, toIdx) + 36f)
                : panelRight - 140f;
            rightAnchorX = Math.Max(panelLeft + 60f, rightAnchorX);

            // Passo 0: Linhas de Rastreio de Defesa no Preço
            for (int i = 0; i < visibleTrackScratch.Count; i++)
            {
                IcebergEvent ev = visibleTrackScratch[i];
                float y = (float)chartScale.GetYByValue(ev.Price);
                if (y < panelTop + 2f || y > panelBottom - 2f) continue;

                float xStart = (ev.BarIndex < fromIdx)
                    ? panelLeft + 2f
                    : Math.Max(panelLeft + 2f, (float)chartControl.GetXByBarIndex(ChartBars, ev.BarIndex));

                float xEnd = ev.TrackActive
                    ? rightAnchorX
                    : Math.Min(panelRight - 6f, (float)chartControl.GetXByBarIndex(ChartBars, Math.Max(fromIdx, Math.Min(toIdx, ev.TrackEndBarIndex))));

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

            double minVol = Math.Max(1.0, chartMinVol);
            double maxRef = Math.Max(minVol + 50.0, Math.Max(LoteGigante * 1.5, chartMinVol * 2.5));

            if (ModoVisual == VeltrixWatchdogModoVisualV9.LateralNoPreco)
            {
                for (int i = 0; i < visibleScratch.Count; i++)
                {
                    IcebergEvent ev = visibleScratch[i];
                    float y = (float)chartScale.GetYByValue(ev.Price);
                    if (y < panelTop + 4f || y > panelBottom - 4f) continue;

                    float xBar = (float)chartControl.GetXByBarIndex(ChartBars, ev.BarIndex);
                    float xStart = Math.Max(panelLeft + 4f, xBar);
                    float xTip = Math.Max(xStart + 18f, rightAnchorX);
                    if (xTip > panelRight - 108f) xTip = panelRight - 108f;

                    var lineBr = ResolveAccentBrush(ev, false);
                    RenderTarget.DrawLine(new SharpDX.Vector2(xStart, y), new SharpDX.Vector2(xTip, y), ResolveTrackBrush(ev), 1.35f);
                    RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(new SharpDX.Vector2(xStart, y), 2.2f, 2.2f), lineBr);

                    DrawIcebergMarkerShape(ev, xTip, y, minVol, maxRef);

                    if (MostrarNumeros)
                    {
                        double norm = Math.Max(0.0, Math.Min(1.0, (ev.Volume - minVol) / Math.Max(10.0, maxRef - minVol)));
                        float radius = 6.0f + (float)(Math.Sqrt(norm) * 14.0);
                        string prefix = (ev.Kind == IcebergKind.Dinamico) ? "D " : "S ";
                        string txt = prefix + ev.Volume.ToString(CultureInfo.InvariantCulture) + " · " + FormatPriceSafe(ev.Price);
                        float pillW = Math.Max(68f, txt.Length * 6.3f + 10f);
                        float pillH = 15f;

                        float boxLeft = Math.Min(panelRight - pillW - 4f, xTip + radius + 8f);
                        float chosenTop = ResolveNonCollidingTop(boxLeft, y, pillW, pillH, panelTop, panelBottom);
                        RenderTarget.DrawLine(new SharpDX.Vector2(xTip + radius + 1f, y), new SharpDX.Vector2(boxLeft, chosenTop + pillH * 0.5f), dxLeaderBrush, 0.85f);
                        DrawPillText(txt, boxLeft, chosenTop, pillW, pillH, lineBr);
                    }
                }
            }
            else
            {
                for (int i = 0; i < visibleScratch.Count; i++)
                {
                    IcebergEvent ev = visibleScratch[i];
                    float x = (float)chartControl.GetXByBarIndex(ChartBars, ev.BarIndex);
                    float y = (float)chartScale.GetYByValue(ev.Price);
                    if (y < panelTop - 30f || y > panelBottom + 30f || x < panelLeft - 30f || x > panelRight + 30f) continue;
                    DrawIcebergMarkerShape(ev, x, y, minVol, maxRef);
                }

                if (MostrarNumeros)
                {
                    for (int i = 0; i < visibleScratch.Count; i++)
                    {
                        IcebergEvent ev = visibleScratch[i];
                        float x = (float)chartControl.GetXByBarIndex(ChartBars, ev.BarIndex);
                        float y = (float)chartScale.GetYByValue(ev.Price);
                        if (y < panelTop - 20f || y > panelBottom + 20f || x < panelLeft - 20f || x > panelRight + 20f) continue;

                        double norm = Math.Max(0.0, Math.Min(1.0, (ev.Volume - minVol) / Math.Max(10.0, maxRef - minVol)));
                        float radius = 6.0f + (float)(Math.Sqrt(norm) * 14.0);

                        string prefix = (ev.Kind == IcebergKind.Dinamico) ? "D " : "S ";
                        string txt = prefix + ev.Volume.ToString(CultureInfo.InvariantCulture);
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
                }
            }

            if (MostrarNumeros)
            {
                for (int i = 0; i < visibleTrackScratch.Count; i++)
                {
                    IcebergEvent ev = visibleTrackScratch[i];
                    if (!ev.TrackActive) continue;
                    float y = (float)chartScale.GetYByValue(ev.Price);
                    if (y < panelTop + 4f || y > panelBottom - 4f) continue;

                    string sideLabel = ev.IsSellSide ? "DEF V " : "DEF C ";
                    string trackTxt = sideLabel + ev.Volume.ToString(CultureInfo.InvariantCulture) + (ev.FollowUpCount > 0 ? " (+" + ev.FollowUpCount + ")" : "");
                    float tW = Math.Max(60f, trackTxt.Length * 6.3f + 10f);
                    float tH = 14f;
                    float tLeft = Math.Max(panelLeft + 4f, Math.Min(panelRight - tW - 4f, rightAnchorX - tW));
                    float tTop = ResolveNonCollidingTop(tLeft, y - 14f, tW, tH, panelTop, panelBottom);

                    DrawPillText(trackTxt, tLeft, tTop, tW, tH, ResolveTrackBrush(ev));
                }
            }

            RenderLiveIcebergsPanel(panelLeft, panelTop, panelRight, panelBottom, chartMinVol, totalDynCount, totalSinCount);
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
            if (dxPanelBg != null) { dxPanelBg.Dispose(); dxPanelBg = null; }
            if (dxPanelBorder != null) { dxPanelBorder.Dispose(); dxPanelBorder = null; }
            if (dxPanelDivider != null) { dxPanelDivider.Dispose(); dxPanelDivider = null; }
            if (dxMutedBrush != null) { dxMutedBrush.Dispose(); dxMutedBrush = null; }
            if (dxBtnBg != null) { dxBtnBg.Dispose(); dxBtnBg = null; }
            if (dxHighlightRowBg != null) { dxHighlightRowBg.Dispose(); dxHighlightRowBg = null; }
            if (dxStrokeDash != null) { dxStrokeDash.Dispose(); dxStrokeDash = null; }
            if (dxStrokeDot != null) { dxStrokeDot.Dispose(); dxStrokeDot = null; }
            if (dxFont != null) { dxFont.Dispose(); dxFont = null; }
            if (dxPanelTitleFmt != null) { dxPanelTitleFmt.Dispose(); dxPanelTitleFmt = null; }
            if (dxPanelBodyFmt != null) { dxPanelBodyFmt.Dispose(); dxPanelBodyFmt = null; }
            if (dxPanelSmallFmt != null) { dxPanelSmallFmt.Dispose(); dxPanelSmallFmt = null; }
            if (dxPanelBtnFmt != null) { dxPanelBtnFmt.Dispose(); dxPanelBtnFmt = null; }
            if (dxFactory != null) { dxFactory.Dispose(); dxFactory = null; }
        }

        public override void OnRenderTargetChanged()
        {
            LimparRecursosRender();
        }

        #region Toolbar & Quick Settings WPF
        private void EnsureToolbarAttachedThrottled()
        {
            if (State == State.Terminated || ChartControl == null || toolbarAttachPending) return;
            DateTime nowUtc = DateTime.UtcNow;
            if ((nowUtc - lastToolbarCheckUtc).TotalMilliseconds < 1400) return;
            lastToolbarCheckUtc = nowUtc;
            toolbarAttachPending = true;
            try
            {
                ChartControl.Dispatcher.InvokeAsync(new Action(() =>
                {
                    toolbarAttachPending = false;
                    if (State == State.Terminated || ChartControl == null) return;
                    Chart ownerChart = ChartControl.OwnerChart;
                    if (ownerChart == null || ownerChart.MainMenu == null) return;
                    attachedOwnerChart = ownerChart;

                    for (int i = 0; i < ownerChart.MainMenu.Count; i++)
                    {
                        FrameworkElement existing = ownerChart.MainMenu[i] as FrameworkElement;
                        if (existing != null && object.Equals(existing.Tag, ToolbarBtnTag))
                            return;
                    }

                    Wpf.Button btn = new Wpf.Button();
                    btn.Tag = ToolbarBtnTag;
                    btn.Content = "❄ Icebergs";
                    btn.ToolTip = "Configurações Rápidas - VeltrixQuant FluentliWatchdog (Filtro ES 800 / NQ 200, Modo Linha Lateral & Painel)";
                    btn.Height = 22;
                    btn.Padding = new Thickness(8, 1, 8, 1);
                    btn.Margin = new Thickness(2, 1, 2, 1);
                    btn.VerticalAlignment = VerticalAlignment.Center;
                    btn.VerticalContentAlignment = VerticalAlignment.Center;
                    btn.FontSize = 11;
                    btn.FontWeight = FontWeights.SemiBold;
                    btn.Cursor = Cursors.Hand;

                    var bg = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(18, 28, 42)); bg.Freeze();
                    var bd = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(56, 189, 248)); bd.Freeze();
                    var fg = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(125, 211, 252)); fg.Freeze();
                    btn.Background = bg;
                    btn.BorderBrush = bd;
                    btn.BorderThickness = new Thickness(1);
                    btn.Foreground = fg;
                    btn.Click += OnToolbarButtonClick;

                    toolbarQuickBtn = btn;
                    ownerChart.MainMenu.Add(btn);
                }));
            }
            catch
            {
                toolbarAttachPending = false;
            }
        }

        private void RemoveToolbarButton()
        {
            Chart owner = attachedOwnerChart;
            Wpf.Button btnRef = toolbarQuickBtn;
            System.Windows.Window winRef = quickSettingsWin;
            attachedOwnerChart = null;
            toolbarQuickBtn = null;
            quickSettingsWin = null;

            ChartControl cc = ChartControl;
            System.Windows.Threading.Dispatcher disp = (cc != null) ? cc.Dispatcher : ((owner != null) ? owner.Dispatcher : null);
            if (disp == null) return;

            try
            {
                disp.InvokeAsync(new Action(() =>
                {
                    try { if (winRef != null) winRef.Close(); } catch { }
                    if (owner != null && owner.MainMenu != null)
                    {
                        bool otherTabActive = false;
                        try
                        {
                            ChartControl activeCc = owner.ActiveChartControl;
                            if (activeCc != null && activeCc != cc && activeCc.Indicators != null)
                            {
                                for (int j = 0; j < activeCc.Indicators.Count; j++)
                                {
                                    FluentliWatchdog sibling = activeCc.Indicators[j] as FluentliWatchdog;
                                    if (sibling != null && sibling != this && sibling.State != State.Terminated)
                                    {
                                        otherTabActive = true;
                                        break;
                                    }
                                }
                            }
                        }
                        catch { }

                        if (!otherTabActive)
                        {
                            for (int i = owner.MainMenu.Count - 1; i >= 0; i--)
                            {
                                FrameworkElement fe = owner.MainMenu[i] as FrameworkElement;
                                if ((btnRef != null && object.ReferenceEquals(fe, btnRef)) || (fe != null && object.Equals(fe.Tag, ToolbarBtnTag)))
                                    owner.MainMenu.RemoveAt(i);
                            }
                        }
                    }
                    if (btnRef != null) btnRef.Click -= OnToolbarButtonClick;
                }));
            }
            catch { }
        }

        private void OnToolbarButtonClick(object sender, RoutedEventArgs e)
        {
            try
            {
                Chart owner = attachedOwnerChart;
                if (owner == null && ChartControl != null) owner = ChartControl.OwnerChart;
                FluentliWatchdog target = this;

                if (owner != null)
                {
                    ChartControl activeCc = owner.ActiveChartControl;
                    if (activeCc != null && activeCc.Indicators != null)
                    {
                        for (int i = 0; i < activeCc.Indicators.Count; i++)
                        {
                            FluentliWatchdog ind = activeCc.Indicators[i] as FluentliWatchdog;
                            if (ind != null && ind.State != State.Terminated)
                            {
                                target = ind;
                                break;
                            }
                        }
                    }
                }
                if (target != null && target.State != State.Terminated)
                    target.OpenQuickSettingsWindow(owner);
            }
            catch { }
        }

        private static string BrushToHex(System.Windows.Media.Brush b, string fallbackHex)
        {
            System.Windows.Media.SolidColorBrush scb = b as System.Windows.Media.SolidColorBrush;
            if (scb == null) return fallbackHex;
            System.Windows.Media.Color c = scb.Color;
            return string.Format(CultureInfo.InvariantCulture, "#{0:X2}{1:X2}{2:X2}", c.R, c.G, c.B);
        }

        private static System.Windows.Media.Brush HexToFrozenBrush(string hex, System.Windows.Media.Brush fallback)
        {
            if (string.IsNullOrWhiteSpace(hex)) return fallback;
            try
            {
                string clean = hex.Trim();
                if (!clean.StartsWith("#")) clean = "#" + clean;
                object parsed = System.Windows.Media.ColorConverter.ConvertFromString(clean);
                if (parsed is System.Windows.Media.Color)
                {
                    var br = new System.Windows.Media.SolidColorBrush((System.Windows.Media.Color)parsed);
                    br.Freeze();
                    return br;
                }
            }
            catch { }
            return fallback;
        }

        private void OpenQuickSettingsWindow(Chart owner)
        {
            if (quickSettingsWin != null)
            {
                try { quickSettingsWin.Activate(); return; }
                catch { quickSettingsWin = null; }
            }

            string instTitle = (Instrument != null && Instrument.MasterInstrument != null) ? Instrument.MasterInstrument.Name : "ATIVO";
            var win = new System.Windows.Window();
            win.Title = "FluentliWatchdog (" + instTitle + ") settings";
            win.SizeToContent = SizeToContent.WidthAndHeight;
            win.ResizeMode = ResizeMode.NoResize;
            win.WindowStyle = WindowStyle.ToolWindow;
            win.WindowStartupLocation = WindowStartupLocation.CenterScreen;
            if (owner != null) win.Owner = owner;

            var winBg = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(18, 22, 33)); winBg.Freeze();
            var cardBg = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(25, 31, 46)); cardBg.Freeze();
            var borderBr = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(56, 130, 175)); borderBr.Freeze();
            var inputBg = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(13, 17, 26)); inputBg.Freeze();
            var txtBr = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(241, 245, 249)); txtBr.Freeze();
            var mutBr = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(160, 185, 210)); mutBr.Freeze();
            var accentBr = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(56, 189, 248)); accentBr.Freeze();
            win.Background = winBg;
            win.Foreground = txtBr;

            var root = new Wpf.StackPanel { Margin = new Thickness(12), MinWidth = 405 };
            root.Children.Add(new Wpf.TextBlock
            {
                Text = "❄ FluentliWatchdog · Icebergs (" + instTitle + " · Filtro Graf: " + ResolveChartPlotThreshold() + ")",
                FontSize = 13,
                FontWeight = FontWeights.Bold,
                Foreground = accentBr,
                Margin = new Thickness(0, 0, 0, 8)
            });

            var cbModo = new Wpf.ComboBox { ItemsSource = Enum.GetValues(typeof(VeltrixWatchdogModoVisualV9)), SelectedItem = ModoVisual, Width = 148 };
            var tbLoteMin = new Wpf.TextBox { Text = LotePequeno.ToString(CultureInfo.InvariantCulture), Width = 68, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbLoteEs = new Wpf.TextBox { Text = LoteMinGraficoES.ToString(CultureInfo.InvariantCulture), Width = 68, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbLoteNq = new Wpf.TextBox { Text = LoteMinGraficoNQ.ToString(CultureInfo.InvariantCulture), Width = 68, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbLoteOut = new Wpf.TextBox { Text = LoteMinGraficoOutros.ToString(CultureInfo.InvariantCulture), Width = 68, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbFiltroMan = new Wpf.TextBox { Text = FiltroGraficoManual.ToString(CultureInfo.InvariantCulture), Width = 68, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbMaxGraf = new Wpf.TextBox { Text = MaxIcebergsNoGrafico.ToString(CultureInfo.InvariantCulture), Width = 68, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbJan = new Wpf.TextBox { Text = JanelaSinteticoSeg.ToString(CultureInfo.InvariantCulture), Width = 68, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var chkNum = new Wpf.CheckBox { IsChecked = MostrarNumeros, Content = "Mostrar Tags e @ Preço", Foreground = txtBr };
            var chkVoz = new Wpf.CheckBox { IsChecked = AtivarVoz, Content = "Alerta de Voz", Foreground = txtBr };
            var chkPainel = new Wpf.CheckBox { IsChecked = MostrarPainelIcebergs, Content = "Painel Dinâmicos / Sintéticos", Foreground = txtBr };
            var cbPos = new Wpf.ComboBox { ItemsSource = Enum.GetValues(typeof(VeltrixWatchdogPosicaoV9)), SelectedItem = GetEffectivePos(), Width = 148 };
            var tbOpac = new Wpf.TextBox { Text = OpacidadePainelPct.ToString(CultureInfo.InvariantCulture), Width = 68, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbOffX = new Wpf.TextBox { Text = OffsetPainelX.ToString(CultureInfo.InvariantCulture), Width = 62, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbOffY = new Wpf.TextBox { Text = OffsetPainelY.ToString(CultureInfo.InvariantCulture), Width = 62, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var chkTrack = new Wpf.CheckBox { IsChecked = AtivarLinhaRastreio, Content = "Linha Rastreio Defesa", Foreground = txtBr };
            var tbTrackLote = new Wpf.TextBox { Text = RastreioLoteMinimo.ToString(CultureInfo.InvariantCulture), Width = 68, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };

            var tbCBuyD = new Wpf.TextBox { Text = BrushToHex(CorCompraDinamico, "#00FA9A"), Width = 86, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbCSellD = new Wpf.TextBox { Text = BrushToHex(CorVendaDinamico, "#DC143C"), Width = 86, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbCBuyS = new Wpf.TextBox { Text = BrushToHex(CorCompraSintetico, "#00FFFF"), Width = 86, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbCSellS = new Wpf.TextBox { Text = BrushToHex(CorVendaSintetico, "#FF8C00"), Width = 86, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbCBg = new Wpf.TextBox { Text = BrushToHex(CorFundoPainel, "#0C101B"), Width = 86, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };
            var tbCBd = new Wpf.TextBox { Text = BrushToHex(CorBordaPainel, "#384C70"), Width = 86, Background = inputBg, Foreground = txtBr, BorderBrush = borderBr, Padding = new Thickness(4, 2, 4, 2) };

            Action applyChanges = () =>
            {
                if (cbModo.SelectedItem is VeltrixWatchdogModoVisualV9)
                    ModoVisual = (VeltrixWatchdogModoVisualV9)cbModo.SelectedItem;
                int iv;
                if (int.TryParse(tbLoteMin.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    LotePequeno = Math.Max(1, Math.Min(10000, iv));
                if (int.TryParse(tbLoteEs.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    LoteMinGraficoES = Math.Max(1, Math.Min(50000, iv));
                if (int.TryParse(tbLoteNq.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    LoteMinGraficoNQ = Math.Max(1, Math.Min(50000, iv));
                if (int.TryParse(tbLoteOut.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    LoteMinGraficoOutros = Math.Max(1, Math.Min(50000, iv));
                if (int.TryParse(tbFiltroMan.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    FiltroGraficoManual = Math.Max(0, Math.Min(50000, iv));
                if (int.TryParse(tbMaxGraf.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    MaxIcebergsNoGrafico = Math.Max(3, Math.Min(50, iv));
                if (int.TryParse(tbJan.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    JanelaSinteticoSeg = Math.Max(2, Math.Min(120, iv));

                MostrarNumeros = (chkNum.IsChecked == true);
                AtivarVoz = (chkVoz.IsChecked == true);
                MostrarPainelIcebergs = (chkPainel.IsChecked == true);
                if (cbPos.SelectedItem is VeltrixWatchdogPosicaoV9)
                    PosicaoPainel = (VeltrixWatchdogPosicaoV9)cbPos.SelectedItem;
                if (int.TryParse(tbOpac.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    OpacidadePainelPct = Math.Max(0, Math.Min(100, iv));
                if (int.TryParse(tbOffX.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    OffsetPainelX = Math.Max(-2000, Math.Min(2000, iv));
                if (int.TryParse(tbOffY.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    OffsetPainelY = Math.Max(-2000, Math.Min(2000, iv));

                AtivarLinhaRastreio = (chkTrack.IsChecked == true);
                if (int.TryParse(tbTrackLote.Text, NumberStyles.Integer, CultureInfo.InvariantCulture, out iv))
                    RastreioLoteMinimo = Math.Max(1, Math.Min(50000, iv));

                CorCompraDinamico = HexToFrozenBrush(tbCBuyD.Text, CorCompraDinamico);
                CorVendaDinamico = HexToFrozenBrush(tbCSellD.Text, CorVendaDinamico);
                CorCompraSintetico = HexToFrozenBrush(tbCBuyS.Text, CorCompraSintetico);
                CorVendaSintetico = HexToFrozenBrush(tbCSellS.Text, CorVendaSintetico);
                CorFundoPainel = HexToFrozenBrush(tbCBg.Text, CorFundoPainel);
                CorBordaPainel = HexToFrozenBrush(tbCBd.Text, CorBordaPainel);

                hasRuntimePosOverride = false;
                lastColorSignature = "";
                if (ChartControl != null) ChartControl.InvalidateVisual();
            };

            var grid = new Wpf.Grid { Margin = new Thickness(0, 2, 0, 8) };
            grid.ColumnDefinitions.Add(new Wpf.ColumnDefinition { Width = new GridLength(195) });
            grid.ColumnDefinitions.Add(new Wpf.ColumnDefinition { Width = GridLength.Auto });

            Action<string, UIElement> addRow = (label, ctrl) =>
            {
                int rIdx = grid.RowDefinitions.Count;
                grid.RowDefinitions.Add(new Wpf.RowDefinition { Height = GridLength.Auto });
                var lbl = new Wpf.TextBlock { Text = label, Foreground = mutBr, FontSize = 11.2, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 2.5, 10, 2.5) };
                Wpf.Grid.SetRow(lbl, rIdx);
                Wpf.Grid.SetColumn(lbl, 0);
                grid.Children.Add(lbl);

                var host = ctrl as FrameworkElement;
                if (host != null) { host.Margin = new Thickness(0, 2.5, 0, 2.5); host.VerticalAlignment = VerticalAlignment.Center; }
                Wpf.Grid.SetRow(ctrl, rIdx);
                Wpf.Grid.SetColumn(ctrl, 1);
                grid.Children.Add(ctrl);
            };

            Func<Wpf.TextBox, Wpf.StackPanel> makeColorRow = (tb) =>
            {
                var sp = new Wpf.StackPanel { Orientation = Wpf.Orientation.Horizontal };
                var sw = new Wpf.Border { Width = 18, Height = 18, CornerRadius = new CornerRadius(3), Margin = new Thickness(0, 0, 6, 0), BorderBrush = borderBr, BorderThickness = new Thickness(1), Background = HexToFrozenBrush(tb.Text, cardBg) };
                tb.TextChanged += (s2, e2) => { sw.Background = HexToFrozenBrush(tb.Text, sw.Background); };
                sp.Children.Add(sw);
                sp.Children.Add(tb);
                return sp;
            };

            addRow("Modo Visual", cbModo);
            addRow("Lote Mínimo Painel (Todos)", tbLoteMin);
            addRow("Filtro Gráfico ES (Auto)", tbLoteEs);
            addRow("Filtro Gráfico NQ (Auto)", tbLoteNq);
            addRow("Filtro Gráfico Outros", tbLoteOut);
            addRow("Filtro Manual (0=Auto)", tbFiltroMan);
            addRow("Máx. Icebergs no Gráfico", tbMaxGraf);
            addRow("Janela Sintético (Seg)", tbJan);
            addRow("Etiquetas", chkNum);
            addRow("Voz", chkVoz);
            addRow("Painel Ao Vivo", chkPainel);
            addRow("Posição Painel", cbPos);
            addRow("Opacidade Painel (%)", tbOpac);

            var offPanel = new Wpf.StackPanel { Orientation = Wpf.Orientation.Horizontal };
            offPanel.Children.Add(tbOffX);
            offPanel.Children.Add(new Wpf.TextBlock { Text = " / ", Foreground = mutBr, VerticalAlignment = VerticalAlignment.Center });
            offPanel.Children.Add(tbOffY);
            var btnResetXY = new Wpf.Button { Content = "Zero", Height = 20, Padding = new Thickness(6, 0, 6, 0), Margin = new Thickness(6, 0, 0, 0), Background = cardBg, Foreground = txtBr, BorderBrush = borderBr, FontSize = 10.5, Cursor = Cursors.Hand };
            btnResetXY.Click += (s2, e2) => { tbOffX.Text = "0"; tbOffY.Text = "0"; applyChanges(); };
            offPanel.Children.Add(btnResetXY);
            addRow("Ajuste Painel X / Y (px)", offPanel);

            addRow("Rastreio Defesa", chkTrack);
            addRow("Lote Mínimo Rastreio", tbTrackLote);
            addRow("Cor Compra Dinâmico", makeColorRow(tbCBuyD));
            addRow("Cor Venda Dinâmico", makeColorRow(tbCSellD));
            addRow("Cor Compra Sintético", makeColorRow(tbCBuyS));
            addRow("Cor Venda Sintético", makeColorRow(tbCSellS));
            addRow("Cor Fundo Painel", makeColorRow(tbCBg));
            addRow("Cor Borda Painel", makeColorRow(tbCBd));

            var scroll = new Wpf.ScrollViewer { MaxHeight = 470, VerticalScrollBarVisibility = Wpf.ScrollBarVisibility.Auto, Content = grid };
            root.Children.Add(new Wpf.Border { Background = cardBg, BorderBrush = borderBr, BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(6), Padding = new Thickness(10, 6, 10, 6), Child = scroll });

            var btnRow = new Wpf.StackPanel { Orientation = Wpf.Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 8, 0, 0) };
            var okBg = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromRgb(14, 116, 144)); okBg.Freeze();
            var btnApply = new Wpf.Button { Content = "Aplicar", Height = 25, Padding = new Thickness(12, 2, 12, 2), Margin = new Thickness(0, 0, 6, 0), Background = okBg, Foreground = txtBr, BorderBrush = accentBr, FontWeight = FontWeights.SemiBold, Cursor = Cursors.Hand };
            var btnOk = new Wpf.Button { Content = "Aplicar & Fechar", Height = 25, Padding = new Thickness(12, 2, 12, 2), Margin = new Thickness(0, 0, 6, 0), Background = cardBg, Foreground = accentBr, BorderBrush = accentBr, FontWeight = FontWeights.SemiBold, Cursor = Cursors.Hand };
            var btnClose = new Wpf.Button { Content = "Fechar", Height = 25, Padding = new Thickness(10, 2, 10, 2), Background = inputBg, Foreground = mutBr, BorderBrush = borderBr, Cursor = Cursors.Hand };

            btnApply.Click += (s2, e2) => { applyChanges(); };
            btnOk.Click += (s2, e2) => { applyChanges(); win.Close(); };
            btnClose.Click += (s2, e2) => { win.Close(); };

            btnRow.Children.Add(btnApply);
            btnRow.Children.Add(btnOk);
            btnRow.Children.Add(btnClose);
            root.Children.Add(btnRow);

            win.Content = root;
            win.Closed += (s2, e2) => { if (object.ReferenceEquals(quickSettingsWin, win)) quickSettingsWin = null; };
            quickSettingsWin = win;
            win.Show();
        }
        #endregion
    }
}
