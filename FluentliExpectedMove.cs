#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.IO;
using System.Xml.Serialization;
using System.Windows.Media;
using System.Net;
using System.Text.RegularExpressions;
using System.Globalization;
using System.Threading.Tasks;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;
#endregion

namespace NinjaTrader.NinjaScript.Indicators
{
    public class FluentliExpectedMove : Indicator
    {
        private double upperBand = 0;
        private double lowerBand = 0;
        private DateTime inicioSessao;
        private double VixInterno = 0.0;
        private double ultimoVixCalculado = 0.0;
        private bool calculouHoje = false;
        private bool sessaoInicializada = false;
        private double precoAberturaSessao = 0;
        private string pastaGexData = @"C:\Users\alanb\Dropbox\Aplicativos\RoboGexNinjaV1";
        private NinjaTrader.Gui.Tools.SimpleFont fonteHud;

        private string painelStatus = "Conectando API Yahoo...";
        private Brush corPainel = Brushes.Gold;

        [NinjaScriptProperty]
        [Display(Name = "1. Puxar VIX Automático da API?", GroupName = "1. Automação do VIX", Order = 1)]
        public bool UsarVixAutomatico { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "2. Volatilidade Manual (fallback/outras classes)", GroupName = "1. Automação do VIX", Order = 2)]
        public double VixManual { get; set; }

        [NinjaScriptProperty]
        [Range(1, 200)]
        [Display(Name = "Espessura da Nuvem (em Ticks)", GroupName = "2. Visual (Mancha)", Order = 1)]
        public int EspessuraNuvem { get; set; }

        [NinjaScriptProperty]
        [Range(1, 100)]
        [Display(Name = "Transparência da Nuvem (1-100%)", GroupName = "2. Visual (Mancha)", Order = 2)]
        public int Opacidade { get; set; }

        [XmlIgnore]
        [Display(Name = "Cor da Nuvem de Venda (Topo)", GroupName = "2. Visual (Mancha)", Order = 3)]
        public Brush CorTopo { get; set; }
        [Browsable(false)]
        public string CorTopoSerializable
        {
            get { return Serialize.BrushToString(CorTopo); }
            set { CorTopo = Serialize.StringToBrush(value); }
        }

        [XmlIgnore]
        [Display(Name = "Cor da Nuvem de Compra (Fundo)", GroupName = "2. Visual (Mancha)", Order = 4)]
        public Brush CorFundo { get; set; }
        [Browsable(false)]
        public string CorFundoSerializable
        {
            get { return Serialize.BrushToString(CorFundo); }
            set { CorFundo = Serialize.StringToBrush(value); }
        }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"Usa o VIX automaticamente apenas em ES/MES. Outros ativos exigem volatilidade manual apropriada.";
                Name = "FluentliExpectedMove";
                Calculate = Calculate.OnBarClose;
                IsOverlay = true;
                DisplayInDataBox = false;

                UsarVixAutomatico = true; 
                VixManual = 15.0; 
                EspessuraNuvem = 12; 
                Opacidade = 20; 

                CorTopo = Brushes.Crimson; 
                CorFundo = Brushes.DodgerBlue; 
            }
            else if (State == State.Historical)
            {
                if (UsarVixAutomatico)
                {
                    // [CORREÇÃO AUDITORIA] Carrega sincronamente a IV do Dropbox (AlvosVolatilidade_*.csv)
                    // para todos os 9 ativos (ES/MES, NQ/MNQ, GC/MGC, CL/MCL, ZB, ZN, YM/MYM, RTY/M2K, NG),
                    // evitando condição de corrida nas barras históricas enquanto o Task.Run do Yahoo roda.
                    bool carregouCsv = TentarCarregarIvDoDropbox();
                    if (IsSp500Instrument())
                    {
                        BuscarVixNaInternet();
                    }
                    else if (!carregouCsv)
                    {
                        if (IsValidVolatility(VixManual))
                        {
                            VixInterno = VixManual;
                            painelStatus = "VOLATILIDADE FALLBACK (" + VixInterno.ToString("F1", CultureInfo.InvariantCulture) + "%)";
                            corPainel = Brushes.Orange;
                        }
                        else
                        {
                            VixInterno = 0;
                            painelStatus = "Sem CSV de IV para " + GetInstrumentName() + "; informe Volatilidade Manual.";
                            corPainel = Brushes.Orange;
                        }
                    }
                }
                else
                {
                    if (IsValidVolatility(VixManual))
                    {
                        VixInterno = VixManual;
                        painelStatus = "VOLATILIDADE MANUAL (" + VixInterno.ToString("F1", CultureInfo.InvariantCulture) + "%)";
                        corPainel = Brushes.Gray;
                    }
                    else
                    {
                        VixInterno = 0;
                        painelStatus = "Valor manual invalido; movimento esperado indisponivel.";
                        corPainel = Brushes.OrangeRed;
                    }
                }
            }
        }

        private string GetInstrumentName()
        {
            return Instrument == null ? "ativo desconhecido" : Instrument.MasterInstrument.Name;
        }

        private string GetNormalizedSymbol()
        {
            string s = GetInstrumentName().ToUpperInvariant();
            if (s.Contains("MES") || s.Contains("ES")) return "ES";
            if (s.Contains("MNQ") || s.Contains("NQ")) return "NQ";
            if (s.Contains("MCL") || s.Contains("CL")) return "CL";
            if (s.Contains("MGC") || s.Contains("GC")) return "GC";
            if (s.Contains("ZN")) return "ZN";
            if (s.Contains("ZB")) return "ZB";
            if (s.Contains("MYM") || s.Contains("YM")) return "YM";
            if (s.Contains("RTY") || s.Contains("M2K")) return "RTY";
            if (s.Contains("MNG") || s.Contains("QG") || s.Contains("NG")) return "NG";
            return s;
        }

        private bool TentarCarregarIvDoDropbox()
        {
            try
            {
                string sym = GetNormalizedSymbol();
                string file = Path.Combine(pastaGexData, "AlvosVolatilidade_" + sym + ".csv");
                if (!File.Exists(file)) return false;
                using (FileStream fs = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (StreamReader sr = new StreamReader(fs))
                {
                    string line = sr.ReadToEnd();
                    if (string.IsNullOrWhiteSpace(line)) return false;
                    var parts = line.Split(',');
                    if (parts.Length < 4) return false;
                    string ivText = parts[3].Replace("%", "").Trim();
                    double parsedIv;
                    if (double.TryParse(ivText, NumberStyles.Any, CultureInfo.InvariantCulture, out parsedIv) && IsValidVolatility(parsedIv))
                    {
                        VixInterno = parsedIv;
                        string sourceLabel = (parts.Length >= 13 && !string.IsNullOrWhiteSpace(parts[12]))
                            ? parts[12].Trim()
                            : "IV Dropbox";
                        painelStatus = sourceLabel.ToUpperInvariant() + " [" + sym + "]: " + VixInterno.ToString("F1", CultureInfo.InvariantCulture) + "%";
                        corPainel = Brushes.Cyan;
                        return true;
                    }
                }
            }
            catch
            {
            }
            return false;
        }

        private bool IsSp500Instrument()
        {
            string symbol = GetInstrumentName();
            return symbol.StartsWith("ES", StringComparison.OrdinalIgnoreCase)
                || symbol.StartsWith("MES", StringComparison.OrdinalIgnoreCase);
        }

        private bool IsValidVolatility(double value)
        {
            return value > 0 && !double.IsNaN(value) && !double.IsInfinity(value);
        }

        private void BuscarVixNaInternet()
        {
            Task.Run(() =>
            {
                try
                {
                    using (WebClient client = new WebClient())
                    {
                        client.Headers.Add("user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)");
                        string json = client.DownloadString("https://query1.finance.yahoo.com/v8/finance/chart/^VIX");
                        Match match = Regex.Match(json, @"""regularMarketPrice"":\s*([\d\.]+)");
                        
                        if (!match.Success)
                            throw new InvalidOperationException("A resposta do Yahoo nao trouxe regularMarketPrice.");

                        double fetchedVix = double.Parse(match.Groups[1].Value, CultureInfo.InvariantCulture);
                        if (!IsValidVolatility(fetchedVix))
                            throw new InvalidOperationException("O Yahoo retornou um VIX invalido.");

                        VixInterno = fetchedVix;
                        painelStatus = "VIX API: ONLINE (" + VixInterno.ToString("F1", CultureInfo.InvariantCulture) + ")";
                        corPainel = Brushes.LimeGreen;
                    }
                }
                catch (Exception ex)
                {
                    if (IsValidVolatility(VixInterno))
                    {
                        // Mantém a IV já carregada do Dropbox (AlvosVolatilidade_ES.csv)
                        return;
                    }
                    if (IsValidVolatility(VixManual))
                    {
                        VixInterno = VixManual;
                        painelStatus = "VIX API falhou (" + ex.Message + "); usando valor manual " + VixManual.ToString("F1", CultureInfo.InvariantCulture);
                        corPainel = Brushes.Red;
                    }
                    else
                    {
                        VixInterno = 0;
                        painelStatus = "VIX API falhou (" + ex.Message + "); sem valor manual valido.";
                        corPainel = Brushes.Red;
                    }
                }
            });
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < 0) return;

            if (!sessaoInicializada || Bars.IsFirstBarOfSession)
            {
                calculouHoje = false;
                inicioSessao = Time[0];
                precoAberturaSessao = Open[0];
                sessaoInicializada = true;
            }
            if (CurrentBar < 1) return;

            // Recalcula também se o Task.Run do Yahoo VIX atualizou VixInterno após a abertura.
            if ((!calculouHoje || Math.Abs(VixInterno - ultimoVixCalculado) > 1e-6) && IsValidVolatility(VixInterno))
            {
                double movimentoDiario = (precoAberturaSessao * (VixInterno / 100.0)) / 16.0;
                upperBand = precoAberturaSessao + movimentoDiario;
                lowerBand = precoAberturaSessao - movimentoDiario;
                ultimoVixCalculado = VixInterno;
                calculouHoje = true;
            }

            if (calculouHoje)
            {
                // [CORREÇÃO AUDITORIA] Draw.Rectangle já aplica o parâmetro `Opacidade` (1-100%)
                // sobre `areaBrush`. Antes, `topoTransparente.Opacity = Opacidade / 100.0` aplicava
                // a opacidade duas vezes (ex.: 20% * 20% = 4%), deixando a nuvem quase invisível.
                double raio = (EspessuraNuvem * TickSize) / 2.0;

                Draw.Rectangle(this, "NuvemTopo", true, inicioSessao, upperBand + raio, Time[0], upperBand - raio, Brushes.Transparent, CorTopo, Opacidade);
                Draw.Rectangle(this, "NuvemFundo", true, inicioSessao, lowerBand + raio, Time[0], lowerBand - raio, Brushes.Transparent, CorFundo, Opacidade);
            }
            else
            {
                RemoveDrawObject("NuvemTopo");
                RemoveDrawObject("NuvemFundo");
            }

            string status = painelStatus;
            if (!IsValidVolatility(VixInterno))
            {
                status += "\nFaixas indisponiveis ate informar volatilidade valida.";
            }
            else if (!UsarVixAutomatico)
            {
                status += "\nValor manual: confirme que representa a volatilidade deste ativo.";
            }
            if (fonteHud == null) fonteHud = new Gui.Tools.SimpleFont("Arial", 12);
            Draw.TextFixed(this, "StatusAPIHUD", status, TextPosition.BottomLeft, corPainel, fonteHud, Brushes.Transparent, Brushes.Transparent, 0);
        }
    }
}

#region NinjaScript generated code. Neither change nor remove.

namespace NinjaTrader.NinjaScript.Indicators
{
	public partial class Indicator : NinjaTrader.Gui.NinjaScript.IndicatorRenderBase
	{
		private FluentliExpectedMove[] cacheFluentliExpectedMove;
		public FluentliExpectedMove FluentliExpectedMove(bool usarVixAutomatico, double vixManual, int espessuraNuvem, int opacidade)
		{
			return FluentliExpectedMove(Input, usarVixAutomatico, vixManual, espessuraNuvem, opacidade);
		}

		public FluentliExpectedMove FluentliExpectedMove(ISeries<double> input, bool usarVixAutomatico, double vixManual, int espessuraNuvem, int opacidade)
		{
			if (cacheFluentliExpectedMove != null)
				for (int idx = 0; idx < cacheFluentliExpectedMove.Length; idx++)
					if (cacheFluentliExpectedMove[idx] != null && cacheFluentliExpectedMove[idx].UsarVixAutomatico == usarVixAutomatico && cacheFluentliExpectedMove[idx].VixManual == vixManual && cacheFluentliExpectedMove[idx].EspessuraNuvem == espessuraNuvem && cacheFluentliExpectedMove[idx].Opacidade == opacidade && cacheFluentliExpectedMove[idx].EqualsInput(input))
						return cacheFluentliExpectedMove[idx];
			return CacheIndicator<FluentliExpectedMove>(new FluentliExpectedMove(){ UsarVixAutomatico = usarVixAutomatico, VixManual = vixManual, EspessuraNuvem = espessuraNuvem, Opacidade = opacidade }, input, ref cacheFluentliExpectedMove);
		}
	}
}

namespace NinjaTrader.NinjaScript.MarketAnalyzerColumns
{
	public partial class MarketAnalyzerColumn : MarketAnalyzerColumnBase
	{
		public Indicators.FluentliExpectedMove FluentliExpectedMove(bool usarVixAutomatico, double vixManual, int espessuraNuvem, int opacidade)
		{
			return indicator.FluentliExpectedMove(Input, usarVixAutomatico, vixManual, espessuraNuvem, opacidade);
		}

		public Indicators.FluentliExpectedMove FluentliExpectedMove(ISeries<double> input , bool usarVixAutomatico, double vixManual, int espessuraNuvem, int opacidade)
		{
			return indicator.FluentliExpectedMove(input, usarVixAutomatico, vixManual, espessuraNuvem, opacidade);
		}
	}
}

namespace NinjaTrader.NinjaScript.Strategies
{
	public partial class Strategy : NinjaTrader.Gui.NinjaScript.StrategyRenderBase
	{
		public Indicators.FluentliExpectedMove FluentliExpectedMove(bool usarVixAutomatico, double vixManual, int espessuraNuvem, int opacidade)
		{
			return indicator.FluentliExpectedMove(Input, usarVixAutomatico, vixManual, espessuraNuvem, opacidade);
		}

		public Indicators.FluentliExpectedMove FluentliExpectedMove(ISeries<double> input , bool usarVixAutomatico, double vixManual, int espessuraNuvem, int opacidade)
		{
			return indicator.FluentliExpectedMove(input, usarVixAutomatico, vixManual, espessuraNuvem, opacidade);
		}
	}
}

#endregion
