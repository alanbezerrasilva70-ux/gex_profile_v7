import os
import tkinter.messagebox as messagebox

# ==============================================================================
# LOCALIZADOR DE PASTA
# ==============================================================================
caminhos = [
    r"C:\NinjaTrader 8\bin\Custom\Indicators",
    os.path.join(os.path.expanduser("~"), "Documents", "NinjaTrader 8", "bin", "Custom", "Indicators")
]
pasta_destino = ""
for p in caminhos:
    if os.path.exists(p):
        pasta_destino = p
        break

if not pasta_destino:
    messagebox.showerror("Erro", "Pasta Indicators não encontrada!")
    exit()

print(f"📂 INSTALANDO DELTA CUMULATIVE PRO EM: {pasta_destino}")

# ==============================================================================
# CÓDIGO: DELTA CUMULATIVE PRO v2.0 (COM NINJASCRIPT GENERATED WRAPPER)
# ==============================================================================
CODE_DELTA = r"""using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Windows;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.Tools;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;

namespace NinjaTrader.NinjaScript.Indicators
{
    public class DeltaCumulativePro : Indicator
    {
        private double sessionDelta = 0;
        private double barDelta = 0;
        private int sessionStartBar = -1;
        
        [NinjaScriptProperty]
        [Display(Name = "Tipo de Visualização", 
                 Description = "Line = Linha continuada | Histogram = Histograma flutuante", 
                 Order = 1, 
                 GroupName = "Configuração")]
        public string TipoVisualizacao { get; set; }
        
        [NinjaScriptProperty]
        [Display(Name = "Escala Delta", 
                 Description = "Multiplicador para visibilidade (1, 10, 100, 1000)", 
                 Order = 2, 
                 GroupName = "Configuração")]
        public int EscalaDelta { get; set; }
        
        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "Cor Delta Positivo", Order = 3, GroupName = "Cores")]
        public Brush CorPositivo { get; set; }
        
        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "Cor Delta Negativo", Order = 4, GroupName = "Cores")]
        public Brush CorNegativo { get; set; }
        
        [Browsable(false)]
        public string CorPositivoSerialize 
        { 
            get { return Serialize.BrushToString(CorPositivo); } 
            set { CorPositivo = Serialize.StringToBrush(value); } 
        }
        
        [Browsable(false)]
        public string CorNegativoSerialize 
        { 
            get { return Serialize.BrushToString(CorNegativo); } 
            set { CorNegativo = Serialize.StringToBrush(value); } 
        }
        
        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "🔴🟢 DELTA CUMULATIVE PRO v2.0 - Fluxo de Agressão (Compatível com Footprint)";
                Name = "DeltaCumulativePro";
                Calculate = Calculate.OnEachTick;
                IsOverlay = false;
                DrawOnPricePanel = false;
                
                TipoVisualizacao = "Line";
                EscalaDelta = 100;
                CorPositivo = Brushes.DodgerBlue;
                CorNegativo = Brushes.Red;
                
                AddPlot(new Stroke(Brushes.Gray, DashStyleHelper.Solid, 2), PlotStyle.Line, "SessionDelta");
                AddLine(Brushes.DarkGray, 0, "ZeroLine");
            }
            else if (State == State.Configure)
            {
                AddDataSeries(BarsPeriodType.Tick, 1);
            }
        }
        
        protected override void OnBarUpdate()
        {
            if (CurrentBars[0] < 0 || CurrentBars[1] < 0) return;
            if (BarsInProgress != 0) return;

            if (sessionStartBar < 0 || (Bars.IsFirstBarOfSession && sessionStartBar != CurrentBar))
            {
                sessionDelta = 0;
                barDelta = 0;
                sessionStartBar = CurrentBar;
            }
            
            Values[0][0] = sessionDelta / (EscalaDelta != 0 ? EscalaDelta : 1);
            
            if (sessionDelta >= 0)
                PlotBrushes[0][0] = CorPositivo;
            else
                PlotBrushes[0][0] = CorNegativo;
        }
        
        protected override void OnMarketData(MarketDataEventArgs e)
        {
            if (BarsInProgress != 0 || e.MarketDataType != MarketDataType.Last) 
                return;
            
            double price = e.Price;
            long volume = e.Volume;
            bool isBuy = false;
            
            if (price >= e.Ask)
                isBuy = true;
            else if (price <= e.Bid)
                isBuy = false;
            else
            {
                if (CurrentBar > 0)
                    isBuy = (price >= Close[0]);
                else
                    return;
            }
            
            if (isBuy)
                sessionDelta += volume;
            else
                sessionDelta -= volume;
            
            barDelta = isBuy ? volume : -volume;
        }
        
        public string GetDeltaInterpretacao()
        {
            if (sessionDelta > 10000) return "🔵 COMPRA EXTREMA";
            if (sessionDelta > 5000) return "🔵 COMPRA FORTE";
            if (sessionDelta > 1000) return "🔵 COMPRA";
            if (sessionDelta > 0) return "🔵 Toque de COMPRA";
            if (sessionDelta < -10000) return "🔴 VENDA EXTREMA";
            if (sessionDelta < -5000) return "🔴 VENDA FORTE";
            if (sessionDelta < -1000) return "🔴 VENDA";
            if (sessionDelta < 0) return "🔴 Toque de VENDA";
            return "⚪ NEUTRO";
        }
    }
}

#region NinjaScript generated code. Neither change nor remove.

namespace NinjaTrader.NinjaScript.Indicators
{
    public partial class Indicator : NinjaTrader.Gui.NinjaScript.IndicatorRenderBase
    {
        private DeltaCumulativePro[] cacheDeltaCumulativePro;

        public DeltaCumulativePro DeltaCumulativePro()
        {
            return DeltaCumulativePro(Input, "Line", 100, Brushes.DodgerBlue, Brushes.Red);
        }

        public DeltaCumulativePro DeltaCumulativePro(ISeries<double> input)
        {
            return DeltaCumulativePro(input, "Line", 100, Brushes.DodgerBlue, Brushes.Red);
        }

        public DeltaCumulativePro DeltaCumulativePro(string tipoVisualizacao, int escalaDelta, Brush corPositivo, Brush corNegativo)
        {
            return DeltaCumulativePro(Input, tipoVisualizacao, escalaDelta, corPositivo, corNegativo);
        }

        public DeltaCumulativePro DeltaCumulativePro(ISeries<double> input, string tipoVisualizacao, int escalaDelta, Brush corPositivo, Brush corNegativo)
        {
            if (cacheDeltaCumulativePro != null)
                for (int idx = 0; idx < cacheDeltaCumulativePro.Length; idx++)
                    if (cacheDeltaCumulativePro[idx] != null && cacheDeltaCumulativePro[idx].TipoVisualizacao == tipoVisualizacao && cacheDeltaCumulativePro[idx].EscalaDelta == escalaDelta && cacheDeltaCumulativePro[idx].CorPositivo == corPositivo && cacheDeltaCumulativePro[idx].CorNegativo == corNegativo && cacheDeltaCumulativePro[idx].EqualsInput(input))
                        return cacheDeltaCumulativePro[idx];
            return CacheIndicator<DeltaCumulativePro>(new DeltaCumulativePro(){ TipoVisualizacao = tipoVisualizacao, EscalaDelta = escalaDelta, CorPositivo = corPositivo, CorNegativo = corNegativo }, input, ref cacheDeltaCumulativePro);
        }
    }
}

namespace NinjaTrader.NinjaScript.MarketAnalyzerColumns
{
    public partial class MarketAnalyzerColumn : MarketAnalyzerColumnBase
    {
        public Indicators.DeltaCumulativePro DeltaCumulativePro()
        {
            return indicator.DeltaCumulativePro(Input, "Line", 100, Brushes.DodgerBlue, Brushes.Red);
        }

        public Indicators.DeltaCumulativePro DeltaCumulativePro(ISeries<double> input)
        {
            return indicator.DeltaCumulativePro(input, "Line", 100, Brushes.DodgerBlue, Brushes.Red);
        }

        public Indicators.DeltaCumulativePro DeltaCumulativePro(string tipoVisualizacao, int escalaDelta, Brush corPositivo, Brush corNegativo)
        {
            return indicator.DeltaCumulativePro(Input, tipoVisualizacao, escalaDelta, corPositivo, corNegativo);
        }

        public Indicators.DeltaCumulativePro DeltaCumulativePro(ISeries<double> input, string tipoVisualizacao, int escalaDelta, Brush corPositivo, Brush corNegativo)
        {
            return indicator.DeltaCumulativePro(input, tipoVisualizacao, escalaDelta, corPositivo, corNegativo);
        }
    }
}

namespace NinjaTrader.NinjaScript.Strategies
{
    public partial class Strategy : NinjaTrader.Gui.NinjaScript.StrategyRenderBase
    {
        public Indicators.DeltaCumulativePro DeltaCumulativePro()
        {
            return indicator.DeltaCumulativePro(Input, "Line", 100, Brushes.DodgerBlue, Brushes.Red);
        }

        public Indicators.DeltaCumulativePro DeltaCumulativePro(ISeries<double> input)
        {
            return indicator.DeltaCumulativePro(input, "Line", 100, Brushes.DodgerBlue, Brushes.Red);
        }

        public Indicators.DeltaCumulativePro DeltaCumulativePro(string tipoVisualizacao, int escalaDelta, Brush corPositivo, Brush corNegativo)
        {
            return indicator.DeltaCumulativePro(Input, tipoVisualizacao, escalaDelta, corPositivo, corNegativo);
        }

        public Indicators.DeltaCumulativePro DeltaCumulativePro(ISeries<double> input, string tipoVisualizacao, int escalaDelta, Brush corPositivo, Brush corNegativo)
        {
            return indicator.DeltaCumulativePro(input, tipoVisualizacao, escalaDelta, corPositivo, corNegativo);
        }
    }
}

#endregion
"""

caminho_final = os.path.join(pasta_destino, "DeltaCumulativePro.cs")
try:
    with open(caminho_final, "w", encoding="utf-8") as f:
        f.write(CODE_DELTA)
    print("✅ DeltaCumulativePro Instalado!")
except Exception as e:
    messagebox.showerror("Erro", str(e))
    exit()

messagebox.showinfo("Sucesso", "✅ DELTA CUMULATIVE PRO INSTALADO!\n\nEste indicador mostra o saldo de agressão do dia.\n\n👉 Aperte F5 no NinjaTrader.\n👉 Adicione ao gráfico (ele vai aparecer num painel novo embaixo).")
