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

print(f"📂 INSTALANDO VWAP INSTITUCIONAL PRO EM: {pasta_destino}")

# ==============================================================================
# CÓDIGO C#: VWAP INSTITUCIONAL PRO (4 BANDAS + NINJASCRIPT GENERATED WRAPPER)
# ==============================================================================
CODE_VWAP = r"""using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
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
    public class VWAPInstitucionalPro : Indicator
    {
        // Variáveis para cálculo acumulativo
        private double sumPV = 0;   // Preço * Volume
        private double sumVol = 0;  // Volume Total
        private double sumP2V = 0;  // Preço^2 * Volume (para Desvio Padrão)
        private double lastBarVolume = 0;
        private int sessionStartBar = -1;
        private int lastProcessedBar = -1;

        [NinjaScriptProperty]
        [Display(Name = "Numero de Bandas", Order = 1, GroupName = "Configuracao")]
        public int NumBandas { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Mostrar Bandas", Order = 2, GroupName = "Configuracao")]
        public bool MostrarBandas { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Reset Diario", Order = 3, GroupName = "Configuracao")]
        public bool ResetDiario { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Multiplicador Desvio Max", Order = 4, GroupName = "Configuracao")]
        public double DesvioMaximo { get; set; }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "VWAP Institucional com 4 Desvios Padrão";
                Name = "VWAPInstitucionalPro";
                Calculate = Calculate.OnEachTick;
                IsOverlay = true;
                DrawOnPricePanel = true;
                ScaleJustification = NinjaTrader.Gui.Chart.ScaleJustification.Right;

                NumBandas = 4;
                MostrarBandas = true;
                ResetDiario = true;
                DesvioMaximo = 3.0;

                // --- PLOTS (LINHAS) ---
                
                // VWAP Central (A Mestra)
                AddPlot(new Stroke(Brushes.Yellow, DashStyleHelper.Solid, 3), PlotStyle.Line, "VWAP");

                // Banda 1 (Valor)
                AddPlot(new Stroke(Brushes.DodgerBlue, DashStyleHelper.Dot, 1), PlotStyle.Line, "Top SD1");
                AddPlot(new Stroke(Brushes.DodgerBlue, DashStyleHelper.Dot, 1), PlotStyle.Line, "Bot SD1");

                // Banda 2 (Valor Extremo)
                AddPlot(new Stroke(Brushes.Cyan, DashStyleHelper.Dash, 2), PlotStyle.Line, "Top SD2");
                AddPlot(new Stroke(Brushes.Cyan, DashStyleHelper.Dash, 2), PlotStyle.Line, "Bot SD2");

                // Banda 3 (Exaustão)
                AddPlot(new Stroke(Brushes.Orange, DashStyleHelper.Solid, 2), PlotStyle.Line, "Top SD3");
                AddPlot(new Stroke(Brushes.Orange, DashStyleHelper.Solid, 2), PlotStyle.Line, "Bot SD3");

                // Banda 4 (Crash/Boom - Reversão Forte)
                AddPlot(new Stroke(Brushes.Red, DashStyleHelper.Solid, 3), PlotStyle.Line, "Top SD4");
                AddPlot(new Stroke(Brushes.Red, DashStyleHelper.Solid, 3), PlotStyle.Line, "Bot SD4");
            }
        }

        protected override void OnBarUpdate()
        {
            // Precisa de pelo menos uma barra
            if (CurrentBar < 0) return;

            if (sessionStartBar < 0 ||
                (ResetDiario && Bars.IsFirstBarOfSession && sessionStartBar != CurrentBar))
            {
                if (sessionStartBar >= 0)
                {
                    sumPV = 0;
                    sumVol = 0;
                    sumP2V = 0;
                }

                sessionStartBar = CurrentBar;
            }

            if (CurrentBar != lastProcessedBar)
            {
                lastBarVolume = 0;
                lastProcessedBar = CurrentBar;
            }

            double typicalPrice = (High[0] + Low[0] + Close[0]) / 3.0;
            double barVolume = Volume[0];
            double volumeDelta = Math.Max(0, barVolume - lastBarVolume);
            lastBarVolume = Math.Max(lastBarVolume, barVolume);

            sumPV += typicalPrice * volumeDelta;
            sumVol += volumeDelta;
            sumP2V += (typicalPrice * typicalPrice) * volumeDelta;

            // Se não tem volume, não tem VWAP
            if (sumVol == 0) return;

            // Fórmula VWAP
            double vwapValue = sumPV / sumVol;

            // Fórmula Desvio Padrão (Variance Method)
            // StdDev = Sqrt( (Sum(P^2 * V) / Sum(V)) - VWAP^2 )
            double variance = (sumP2V / sumVol) - (vwapValue * vwapValue);
            // Proteção contra números negativos (erro de arredondamento)
            if (variance < 0) variance = 0;
            double stdDevValue = Math.Sqrt(variance);

            Values[0][0] = vwapValue;

            if (MostrarBandas)
            {
                // Bandas Superiores (VWAP + N * Desvio)
                if (NumBandas >= 1) Values[1][0] = vwapValue + (1.0 * stdDevValue); // SD1
                if (NumBandas >= 2) Values[3][0] = vwapValue + (2.0 * stdDevValue); // SD2
                if (NumBandas >= 3) Values[5][0] = vwapValue + (3.0 * stdDevValue); // SD3
                if (NumBandas >= 4) Values[7][0] = vwapValue + (4.0 * stdDevValue); // SD4

                // Bandas Inferiores (VWAP - N * Desvio)
                if (NumBandas >= 1) Values[2][0] = vwapValue - (1.0 * stdDevValue); // SD1
                if (NumBandas >= 2) Values[4][0] = vwapValue - (2.0 * stdDevValue); // SD2
                if (NumBandas >= 3) Values[6][0] = vwapValue - (3.0 * stdDevValue); // SD3
                if (NumBandas >= 4) Values[8][0] = vwapValue - (4.0 * stdDevValue); // SD4
            }
        }
    }
}

#region NinjaScript generated code. Neither change nor remove.

namespace NinjaTrader.NinjaScript.Indicators
{
    public partial class Indicator : NinjaTrader.Gui.NinjaScript.IndicatorRenderBase
    {
        private VWAPInstitucionalPro[] cacheVWAPInstitucionalPro;

        public VWAPInstitucionalPro VWAPInstitucionalPro()
        {
            return VWAPInstitucionalPro(Input, 4, true, true, 3.0);
        }

        public VWAPInstitucionalPro VWAPInstitucionalPro(ISeries<double> input)
        {
            return VWAPInstitucionalPro(input, 4, true, true, 3.0);
        }

        public VWAPInstitucionalPro VWAPInstitucionalPro(int numBandas, bool mostrarBandas, bool resetDiario, double desvioMaximo)
        {
            return VWAPInstitucionalPro(Input, numBandas, mostrarBandas, resetDiario, desvioMaximo);
        }

        public VWAPInstitucionalPro VWAPInstitucionalPro(ISeries<double> input, int numBandas, bool mostrarBandas, bool resetDiario, double desvioMaximo)
        {
            if (cacheVWAPInstitucionalPro != null)
                for (int idx = 0; idx < cacheVWAPInstitucionalPro.Length; idx++)
                    if (cacheVWAPInstitucionalPro[idx] != null && cacheVWAPInstitucionalPro[idx].NumBandas == numBandas && cacheVWAPInstitucionalPro[idx].MostrarBandas == mostrarBandas && cacheVWAPInstitucionalPro[idx].ResetDiario == resetDiario && cacheVWAPInstitucionalPro[idx].DesvioMaximo == desvioMaximo && cacheVWAPInstitucionalPro[idx].EqualsInput(input))
                        return cacheVWAPInstitucionalPro[idx];
            return CacheIndicator<VWAPInstitucionalPro>(new VWAPInstitucionalPro() { NumBandas = numBandas, MostrarBandas = mostrarBandas, ResetDiario = resetDiario, DesvioMaximo = desvioMaximo }, input, ref cacheVWAPInstitucionalPro);
        }
    }
}

namespace NinjaTrader.NinjaScript.MarketAnalyzerColumns
{
    public partial class MarketAnalyzerColumn : MarketAnalyzerColumnBase
    {
        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro()
        {
            return indicator.VWAPInstitucionalPro(Input, 4, true, true, 3.0);
        }

        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro(ISeries<double> input)
        {
            return indicator.VWAPInstitucionalPro(input, 4, true, true, 3.0);
        }

        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro(int numBandas, bool mostrarBandas, bool resetDiario, double desvioMaximo)
        {
            return indicator.VWAPInstitucionalPro(Input, numBandas, mostrarBandas, resetDiario, desvioMaximo);
        }

        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro(ISeries<double> input, int numBandas, bool mostrarBandas, bool resetDiario, double desvioMaximo)
        {
            return indicator.VWAPInstitucionalPro(input, numBandas, mostrarBandas, resetDiario, desvioMaximo);
        }
    }
}

namespace NinjaTrader.NinjaScript.Strategies
{
    public partial class Strategy : NinjaTrader.Gui.NinjaScript.StrategyRenderBase
    {
        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro()
        {
            return indicator.VWAPInstitucionalPro(Input, 4, true, true, 3.0);
        }

        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro(ISeries<double> input)
        {
            return indicator.VWAPInstitucionalPro(input, 4, true, true, 3.0);
        }

        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro(int numBandas, bool mostrarBandas, bool resetDiario, double desvioMaximo)
        {
            return indicator.VWAPInstitucionalPro(Input, numBandas, mostrarBandas, resetDiario, desvioMaximo);
        }

        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro(ISeries<double> input, int numBandas, bool mostrarBandas, bool resetDiario, double desvioMaximo)
        {
            return indicator.VWAPInstitucionalPro(input, numBandas, mostrarBandas, resetDiario, desvioMaximo);
        }
    }
}

#endregion
"""

caminho_final = os.path.join(pasta_destino, "VWAPInstitucionalPro.cs")
try:
    with open(caminho_final, "w", encoding="utf-8") as f:
        f.write(CODE_VWAP)
    print("✅ VWAP Instalada com Sucesso!")
except Exception as e:
    messagebox.showerror("Erro", str(e))
    exit()

messagebox.showinfo("Sucesso V66", "✅ O PACOTE ESTÁ COMPLETO!\n\nInstalei o 'VWAPInstitucionalPro'.\n\n1. Linha Amarela Grossa = Preço Justo (VWAP).\n2. Bandas Vermelhas (SD4) = Pontos de Reversão Extrema.\n\n👉 Dê F5 e adicione ao gráfico.")
