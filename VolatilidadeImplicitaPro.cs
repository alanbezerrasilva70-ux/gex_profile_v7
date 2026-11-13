using System;
using System.IO;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Windows; 
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Tools; 
using NinjaTrader.Gui.Chart;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;

namespace NinjaTrader.NinjaScript.Indicators
{
    public class VolatilidadeImplicitaPro : Indicator
    {
        private DateTime ultimaLeitura = DateTime.MinValue;
        private string pastaIvData = @"C:\Users\alanb\Dropbox\Aplicativos\RoboGexNinjaV1"; 
        
        private double ivVal = 0;
        private string ivSource = "IV sem dados";
        private SimpleFont fonteLabels;
        private int sessionStartBar = -1;
        private double sessionAnchorPrice = 0;

        #region Parâmetros de Menu (UI NinjaTrader)
        
        [NinjaScriptProperty]
        [Display(Name="IV Manual (Se 0, lê do Dropbox)", Order=1, GroupName="1. Parâmetros Base")]
        public double IvManual { get; set; }

        [NinjaScriptProperty]
        [Display(Name="Linha UP (+68%)", Order=1, GroupName="2. Visual: Bandas 1 SD")]
        public Stroke LinhaUp1 { get; set; }

        [NinjaScriptProperty]
        [Display(Name="Linha DOWN (-68%)", Order=2, GroupName="2. Visual: Bandas 1 SD")]
        public Stroke LinhaDn1 { get; set; }

        [NinjaScriptProperty]
        [Display(Name="Linha UP (+95%)", Order=1, GroupName="3. Visual: Bandas 2 SD")]
        public Stroke LinhaUp2 { get; set; }

        [NinjaScriptProperty]
        [Display(Name="Linha DOWN (-95%)", Order=2, GroupName="3. Visual: Bandas 2 SD")]
        public Stroke LinhaDn2 { get; set; }

        [NinjaScriptProperty]
        [Display(Name="Linha UP (+99%)", Order=1, GroupName="4. Visual: Bandas 3 SD")]
        public Stroke LinhaUp3 { get; set; }

        [NinjaScriptProperty]
        [Display(Name="Linha DOWN (-99%)", Order=2, GroupName="4. Visual: Bandas 3 SD")]
        public Stroke LinhaDn3 { get; set; }

        #endregion

        protected override void OnStateChange() {
            if (State == State.SetDefaults) {
                Name = "VolatilidadeImplicitaPro"; 
                Description = "Plota faixas estimadas de 1, 2 e 3 desvios da IV-base, ancoradas na abertura da sessão.";
                Calculate = Calculate.OnEachTick; 
                IsOverlay = true;
                IvManual = 0;

                // Valores e cores padrão ao carregar no gráfico pela primeira vez
                LinhaUp1 = new Stroke(Brushes.LimeGreen, DashStyleHelper.Dash, 2);
                LinhaDn1 = new Stroke(Brushes.Crimson, DashStyleHelper.Dash, 2);
                LinhaUp2 = new Stroke(Brushes.DarkGreen, DashStyleHelper.Solid, 2);
                LinhaDn2 = new Stroke(Brushes.DarkRed, DashStyleHelper.Solid, 2);
                LinhaUp3 = new Stroke(Brushes.Magenta, DashStyleHelper.Solid, 3);
                LinhaDn3 = new Stroke(Brushes.Magenta, DashStyleHelper.Solid, 3);
            }
        }

        protected override void OnBarUpdate() {
            if (CurrentBar < 0) return;

            if (sessionStartBar < 0 ||
                (Bars.IsFirstBarOfSession && sessionStartBar != CurrentBar)) {
                sessionStartBar = CurrentBar;
                sessionAnchorPrice = Open[0];
            }
            if (CurrentBar < 1) return;
            
            // Lê o arquivo CSV a cada 5 segundos para não travar o NinjaTrader
            if (DateTime.Now > ultimaLeitura.AddSeconds(5)) { 
                LerCSV(); 
                ultimaLeitura = DateTime.Now; 
                if (State == State.Realtime) ForceRefresh(); 
            }

            if(fonteLabels == null) fonteLabels = new SimpleFont("Arial", 9);
            bool manualIVRequested = IvManual != 0;
            bool manualIVValid = IvManual > 0 && !double.IsNaN(IvManual) && !double.IsInfinity(IvManual);
            if (manualIVRequested && !manualIVValid) {
                Draw.TextFixed(this, "IVSourceHUD", "IV manual invalida", TextPosition.TopRight, Brushes.OrangeRed, fonteLabels, Brushes.Transparent, Brushes.Transparent, 0);
                RemoverFaixas();
                return;
            }

            double currentIV = manualIVValid
                ? IvManual
                : ivVal;

            if (currentIV > 0 && !double.IsNaN(currentIV) && !double.IsInfinity(currentIV)) {
                string source = manualIVValid ? "IV MANUAL" : ivSource.ToUpperInvariant();
                Draw.TextFixed(this, "IVSourceHUD", source + ": " + currentIV.ToString("F1") + "%", TextPosition.TopRight, Brushes.White, fonteLabels, Brushes.Transparent, Brushes.Transparent, 0);
                
                double p = sessionAnchorPrice;
                
                // MÁGICA MATEMÁTICA: currentIV / 1600 equivale a (IV / 100) / sqrt(252 dias)
                double dem = p * (currentIV / 1600.0); 

                double up1 = p + dem;
                double dn1 = p - dem;
                double up2 = p + (dem * 2);
                double dn2 = p - (dem * 2);
                double up3 = p + (dem * 3);
                double dn3 = p - (dem * 3);

                // Desenha 1 SD (Convertendo a espessura para INT para resolver o erro)
                Draw.HorizontalLine(this, "UP1", up1, LinhaUp1.Brush, LinhaUp1.DashStyleHelper, (int)LinhaUp1.Width);
                Draw.Text(this, "TxtUP1", false, "1 SD (+68%) [" + up1.ToString("F2") + "]", -10, up1, 10, LinhaUp1.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);
                
                Draw.HorizontalLine(this, "DN1", dn1, LinhaDn1.Brush, LinhaDn1.DashStyleHelper, (int)LinhaDn1.Width);
                Draw.Text(this, "TxtDN1", false, "-1 SD (-68%) [" + dn1.ToString("F2") + "]", -10, dn1, -10, LinhaDn1.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);

                // Desenha 2 SD
                Draw.HorizontalLine(this, "UP2", up2, LinhaUp2.Brush, LinhaUp2.DashStyleHelper, (int)LinhaUp2.Width);
                Draw.Text(this, "TxtUP2", false, "2 SD (+95%) [" + up2.ToString("F2") + "]", -10, up2, 10, LinhaUp2.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);
                
                Draw.HorizontalLine(this, "DN2", dn2, LinhaDn2.Brush, LinhaDn2.DashStyleHelper, (int)LinhaDn2.Width);
                Draw.Text(this, "TxtDN2", false, "-2 SD (-95%) [" + dn2.ToString("F2") + "]", -10, dn2, -10, LinhaDn2.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);

                // Desenha 3 SD
                Draw.HorizontalLine(this, "UP3", up3, LinhaUp3.Brush, LinhaUp3.DashStyleHelper, (int)LinhaUp3.Width);
                Draw.Text(this, "TxtUP3", false, "3 SD (+99% MAX) [" + up3.ToString("F2") + "]", -10, up3, 10, LinhaUp3.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);
                
                Draw.HorizontalLine(this, "DN3", dn3, LinhaDn3.Brush, LinhaDn3.DashStyleHelper, (int)LinhaDn3.Width);
                Draw.Text(this, "TxtDN3", false, "-3 SD (-99% MAX) [" + dn3.ToString("F2") + "]", -10, dn3, -10, LinhaDn3.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);
            }
            else
            {
                RemoveDrawObject("IVSourceHUD");
                RemoverFaixas();
            }
        }

        private void RemoverFaixas() {
            string[] tags = {
                "UP1", "TxtUP1", "DN1", "TxtDN1",
                "UP2", "TxtUP2", "DN2", "TxtDN2",
                "UP3", "TxtUP3", "DN3", "TxtDN3"
            };
            foreach (string tag in tags) RemoveDrawObject(tag);
        }

        private void LerCSV() {
            try {
                if (Instrument == null) return; 
                string s = Instrument.MasterInstrument.Name;
                
                if(s.Contains("MES") || s.Contains("ES")) s="ES"; 
                else if(s.Contains("MNQ") || s.Contains("NQ")) s="NQ"; 
                else if(s.Contains("MCL") || s.Contains("CL")) s="CL";
                else if(s.Contains("MGC") || s.Contains("GC")) s="GC"; 
                else if(s.Contains("ZN")) s="ZN";
                else if(s.Contains("ZB")) s="ZB";
                else if(s.Contains("MYM") || s.Contains("YM")) s="YM";
                else if(s.Contains("RTY") || s.Contains("M2K")) s="RTY";
                else if(s.Contains("MNG") || s.Contains("QG") || s.Contains("NG")) s="NG";

                string file = Path.Combine(pastaIvData, "AlvosVolatilidade_" + s + ".csv");
                if (!File.Exists(file)) {
                    ivVal = 0;
                    ivSource = "IV sem dados";
                    return;
                }
                using (FileStream fs = new FileStream(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (StreamReader sr = new StreamReader(fs))
                {
                    string line = sr.ReadToEnd();
                    if (string.IsNullOrWhiteSpace(line)) return; // Preserva leitura anterior durante sync do Dropbox
                    var lines = line.Split(',');
                    if (lines.Length >= 4) {
                        string ivString = lines[3].Replace("%", "").Trim();
                        double parsedIv;
                        if (double.TryParse(ivString, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out parsedIv)
                            && !double.IsNaN(parsedIv) && !double.IsInfinity(parsedIv) && parsedIv > 0) {
                            ivVal = parsedIv;
                            ivSource = (lines.Length >= 13 && !string.IsNullOrWhiteSpace(lines[12]))
                                ? lines[12].Trim()
                                : "IV base assumida";
                        } else if (ivVal <= 0) {
                            ivSource = "IV invalida no CSV";
                            Print("VolatilidadeImplicitaPro: valor de IV invalido em " + file);
                        }
                    }
                }
            } catch (Exception ex) {
                if (ivVal <= 0) {
                    ivSource = "Erro lendo IV: " + ex.Message;
                }
                Print("VolatilidadeImplicitaPro: " + ex.Message);
            }
        }
    }
}

#region NinjaScript generated code. Neither change nor remove.

namespace NinjaTrader.NinjaScript.Indicators
{
	public partial class Indicator : NinjaTrader.Gui.NinjaScript.IndicatorRenderBase
	{
		private VolatilidadeImplicitaPro[] cacheVolatilidadeImplicitaPro;
		public VolatilidadeImplicitaPro VolatilidadeImplicitaPro(double ivManual, Stroke linhaUp1, Stroke linhaDn1, Stroke linhaUp2, Stroke linhaDn2, Stroke linhaUp3, Stroke linhaDn3)
		{
			return VolatilidadeImplicitaPro(Input, ivManual, linhaUp1, linhaDn1, linhaUp2, linhaDn2, linhaUp3, linhaDn3);
		}

		public VolatilidadeImplicitaPro VolatilidadeImplicitaPro(ISeries<double> input, double ivManual, Stroke linhaUp1, Stroke linhaDn1, Stroke linhaUp2, Stroke linhaDn2, Stroke linhaUp3, Stroke linhaDn3)
		{
			if (cacheVolatilidadeImplicitaPro != null)
				for (int idx = 0; idx < cacheVolatilidadeImplicitaPro.Length; idx++)
					if (cacheVolatilidadeImplicitaPro[idx] != null && cacheVolatilidadeImplicitaPro[idx].IvManual == ivManual && cacheVolatilidadeImplicitaPro[idx].LinhaUp1 == linhaUp1 && cacheVolatilidadeImplicitaPro[idx].LinhaDn1 == linhaDn1 && cacheVolatilidadeImplicitaPro[idx].LinhaUp2 == linhaUp2 && cacheVolatilidadeImplicitaPro[idx].LinhaDn2 == linhaDn2 && cacheVolatilidadeImplicitaPro[idx].LinhaUp3 == linhaUp3 && cacheVolatilidadeImplicitaPro[idx].LinhaDn3 == linhaDn3 && cacheVolatilidadeImplicitaPro[idx].EqualsInput(input))
						return cacheVolatilidadeImplicitaPro[idx];
			return CacheIndicator<VolatilidadeImplicitaPro>(new VolatilidadeImplicitaPro(){ IvManual = ivManual, LinhaUp1 = linhaUp1, LinhaDn1 = linhaDn1, LinhaUp2 = linhaUp2, LinhaDn2 = linhaDn2, LinhaUp3 = linhaUp3, LinhaDn3 = linhaDn3 }, input, ref cacheVolatilidadeImplicitaPro);
		}
	}
}

namespace NinjaTrader.NinjaScript.MarketAnalyzerColumns
{
	public partial class MarketAnalyzerColumn : MarketAnalyzerColumnBase
	{
		public Indicators.VolatilidadeImplicitaPro VolatilidadeImplicitaPro(double ivManual, Stroke linhaUp1, Stroke linhaDn1, Stroke linhaUp2, Stroke linhaDn2, Stroke linhaUp3, Stroke linhaDn3)
		{
			return indicator.VolatilidadeImplicitaPro(Input, ivManual, linhaUp1, linhaDn1, linhaUp2, linhaDn2, linhaUp3, linhaDn3);
		}

		public Indicators.VolatilidadeImplicitaPro VolatilidadeImplicitaPro(ISeries<double> input , double ivManual, Stroke linhaUp1, Stroke linhaDn1, Stroke linhaUp2, Stroke linhaDn2, Stroke linhaUp3, Stroke linhaDn3)
		{
			return indicator.VolatilidadeImplicitaPro(input, ivManual, linhaUp1, linhaDn1, linhaUp2, linhaDn2, linhaUp3, linhaDn3);
		}
	}
}

namespace NinjaTrader.NinjaScript.Strategies
{
	public partial class Strategy : NinjaTrader.Gui.NinjaScript.StrategyRenderBase
	{
		public Indicators.VolatilidadeImplicitaPro VolatilidadeImplicitaPro(double ivManual, Stroke linhaUp1, Stroke linhaDn1, Stroke linhaUp2, Stroke linhaDn2, Stroke linhaUp3, Stroke linhaDn3)
		{
			return indicator.VolatilidadeImplicitaPro(Input, ivManual, linhaUp1, linhaDn1, linhaUp2, linhaDn2, linhaUp3, linhaDn3);
		}

		public Indicators.VolatilidadeImplicitaPro VolatilidadeImplicitaPro(ISeries<double> input , double ivManual, Stroke linhaUp1, Stroke linhaDn1, Stroke linhaUp2, Stroke linhaDn2, Stroke linhaUp3, Stroke linhaDn3)
		{
			return indicator.VolatilidadeImplicitaPro(input, ivManual, linhaUp1, linhaDn1, linhaUp2, linhaDn2, linhaUp3, linhaDn3);
		}
	}
}

#endregion
