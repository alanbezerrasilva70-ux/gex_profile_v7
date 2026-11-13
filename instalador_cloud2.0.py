import os
import tkinter.messagebox as messagebox

# ==============================================================================
# 1. LOCALIZADOR INTELIGENTE DE PASTA (NinjaTrader 8)
# ==============================================================================
caminhos = [
    r"C:\Users\alanb\OneDrive\Documentos\NinjaTrader 8\bin\Custom\Indicators",
   
    os.path.join(os.path.expanduser("~"), "Documents", "NinjaTrader 8", "bin", "Custom", "Indicators")
]
pasta_destino = ""
for p in caminhos:
    if os.path.exists(p):
        pasta_destino = p
        break

if not pasta_destino:
    messagebox.showerror("Erro Crítico", "Pasta 'Custom/Indicators' do NinjaTrader não encontrada!")
    exit()

print(f"📂 PASTA DETECTADA: {pasta_destino}")
print("🔨 INICIANDO COMPILAÇÃO DOS ARQUIVOS PREMIUM...")

# ==============================================================================
# ARQUIVO 1: NiveisEstruturaPro (Histograma Gamma) - Fonte: Original v1
# ==============================================================================
CODE_ESTRUTURA = r"""
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.IO;
using System.Windows.Media;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.NinjaScript;
using SharpDX;
using SharpDX.Direct2D1;
using SharpDX.DirectWrite;

namespace NinjaTrader.NinjaScript.Indicators
{
    public class NiveisEstruturaPro : Indicator
    {
        public class GammaLevel { public double Strike; public double NetGamma; public string Label; }
        private List<GammaLevel> niveisGamma = new List<GammaLevel>();
        private DateTime ultimaLeitura = DateTime.MinValue;
        private string pastaGexData = @"C:\Users\alanb\Dropbox\Aplicativos\RoboGexNinjaV1";
        
        private SharpDX.Direct2D1.Brush dxBrushCall, dxBrushPut, dxBrushText, dxBrushHighlight, dxBrushCallHeavy, dxBrushPutHeavy;
        private SharpDX.DirectWrite.TextFormat dxTextFormat, dxTextFormatBold;

        [NinjaScriptProperty] [Display(Name="Opacidade (%)", Order=1, GroupName="Visual")] public int Opacidade { get; set; }
        [NinjaScriptProperty] [Display(Name="Largura Max", Order=2, GroupName="Visual")] public int LarguraMax { get; set; }

        protected override void OnStateChange() {
            if (State == State.SetDefaults) {
                Name = "NiveisEstruturaPro"; Calculate = Calculate.OnEachTick; IsOverlay = true;
                Opacidade = 40; LarguraMax = 300;
            } else if (State == State.DataLoaded) LerTudo();
        }

        protected override void OnBarUpdate() {
            if (DateTime.Now > ultimaLeitura.AddSeconds(5)) { LerTudo(); ultimaLeitura = DateTime.Now; ForceRefresh(); }
        }

        protected override void OnRender(ChartControl chartControl, ChartScale chartScale) {
            if (niveisGamma.Count == 0 || chartControl == null) return;
            if (dxBrushCall == null) dxBrushCall = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0f, 1f, 0f, Opacidade/100f));
            if (dxBrushPut == null) dxBrushPut = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1f, 0f, 0f, Opacidade/100f));
            if (dxBrushCallHeavy == null) dxBrushCallHeavy = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0f, 0.8f, 0f, 1f));
            if (dxBrushPutHeavy == null) dxBrushPutHeavy = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.7f, 0f, 0f, 1f));
            if (dxBrushText == null) dxBrushText = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1f, 1f, 1f, 1f));
            if (dxBrushHighlight == null) dxBrushHighlight = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1f, 1f, 0f, 1f));
            if (dxTextFormat == null) dxTextFormat = new TextFormat(new SharpDX.DirectWrite.Factory(), "Arial", SharpDX.DirectWrite.FontWeight.Normal, SharpDX.DirectWrite.FontStyle.Normal, 10);
            if (dxTextFormatBold == null) dxTextFormatBold = new TextFormat(new SharpDX.DirectWrite.Factory(), "Arial", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 11);

            double maxG = 0;
            foreach(var n in niveisGamma) if(Math.Abs(n.NetGamma) > maxG) maxG = Math.Abs(n.NetGamma);
            if (maxG == 0) return;

            float canvasW = (float)chartControl.ActualWidth;
            float canvasH = (float)chartControl.ActualHeight;

            foreach (var n in niveisGamma) {
                float y = (float)chartScale.GetYByValue(n.Strike);
                if (y < -20 || y > canvasH + 20) continue;
                double ratio = Math.Abs(n.NetGamma)/maxG;
                float w = (float)(ratio * LarguraMax);
                if (w < 2) continue;
                float h = (ratio > 0.5) ? 6 : 4;
                SharpDX.RectangleF rect = new SharpDX.RectangleF(canvasW - w, y - h/2, w, h);
                if (n.NetGamma > 0) {
                    if (ratio > 0.70) RenderTarget.FillRectangle(rect, dxBrushCallHeavy);
                    else RenderTarget.FillRectangle(rect, dxBrushCall);
                } else {
                    if (ratio > 0.70) RenderTarget.FillRectangle(rect, dxBrushPutHeavy);
                    else RenderTarget.FillRectangle(rect, dxBrushPut);
                }

                // [CORREÇÃO 9] A coluna `ng` do GammaProfile_*.csv já está em dólares
                // (coi/poi * gamma * mult * spot). Multiplicar de novo por 100 * Close[0]
                // inflava o valor em ~760.000x no ES.
                string txt = FormatVal(n.NetGamma); 
                if (!string.IsNullOrEmpty(n.Label)) {
                    txt = n.Label + " " + txt;
                    float tw = txt.Length * 8;
                    RenderTarget.DrawText(txt, dxTextFormatBold, new SharpDX.RectangleF(canvasW - w - tw - 25, y - 10, tw + 25, 20), dxBrushHighlight);
                } else if (ratio > 0.25) {
                    float tw = txt.Length * 6;
                    RenderTarget.DrawText(txt, dxTextFormat, new SharpDX.RectangleF(canvasW - w - tw - 10, y - 7, tw + 10, 15), dxBrushText);
                }
            }
        }
        
        public override void OnRenderTargetChanged() {
            if(dxBrushCall!=null) dxBrushCall.Dispose(); dxBrushCall=null;
            if(dxBrushPut!=null) dxBrushPut.Dispose(); dxBrushPut=null;
            if(dxBrushCallHeavy!=null) dxBrushCallHeavy.Dispose(); dxBrushCallHeavy=null;
            if(dxBrushPutHeavy!=null) dxBrushPutHeavy.Dispose(); dxBrushPutHeavy=null;
            if(dxBrushText!=null) dxBrushText.Dispose(); dxBrushText=null;
            if(dxBrushHighlight!=null) dxBrushHighlight.Dispose(); dxBrushHighlight=null;
            if(dxTextFormat!=null) dxTextFormat.Dispose(); dxTextFormat=null;
            if(dxTextFormatBold!=null) dxTextFormatBold.Dispose(); dxTextFormatBold=null;
        }

        private void LerTudo() {
            try {
                if(Instrument==null)return;
                string s = Instrument.MasterInstrument.Name;
                if(s.Contains("ES"))s="ES"; 
                else if(s.Contains("NQ"))s="NQ"; 
                else if(s.Contains("GC"))s="GC"; 
                else if(s.Contains("CL"))s="CL"; 
                else if(s.Contains("ZB"))s="ZB"; 
                else if(s.Contains("ZN"))s="ZN";
                else if(s.Contains("YM"))s="YM";
                else if(s.Contains("RTY") || s.Contains("M2K"))s="RTY";
                else if(s.Contains("NG") || s.Contains("QG"))s="NG";

                var novos = new List<GammaLevel>();
                var map = new System.Collections.Generic.Dictionary<double,string>();
                string f1 = Path.Combine(pastaGexData, "NiveisGamma_"+s+".csv");
                if(File.Exists(f1)) {
                    var p = File.ReadAllText(f1).Split(',');
                    if(p.Length>=5) { AddL(map, p[0], "CW"); AddL(map, p[1], "PW"); AddL(map, p[2], "ZG"); }
                }
                string f2 = Path.Combine(pastaGexData, "GammaProfile_"+s+".csv");
                if(File.Exists(f2)) {
                    using(var sr = new StreamReader(f2)) {
                        sr.ReadLine();
                        while(!sr.EndOfStream) {
                            var ln = sr.ReadLine().Split(',');
                            if(ln.Length>=2) {
                                double st, ng;
                                if(double.TryParse(ln[0], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out st) &&
                                   double.TryParse(ln[1], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out ng)) {
                                    string lb = map.ContainsKey(st) ? map[st] : "";
                                    novos.Add(new GammaLevel{Strike=st, NetGamma=ng, Label=lb});
                                }
                            }
                        }
                    }
                }
                if(novos.Count>0) niveisGamma=novos;
            } catch{}
        }
        private void AddL(System.Collections.Generic.Dictionary<double,string> d, string v, string t) {
            if(double.TryParse(v, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out double val)) d[val]=t;
        }
        private string FormatVal(double v) {
            double a = Math.Abs(v); string s = v<0?"-":"";
            if(a>=1e9) return s+"$"+(a/1e9).ToString("F1")+"B";
            if(a>=1e6) return s+"$"+(a/1e6).ToString("F1")+"M";
            return "";
        }
    }
}
"""

# ==============================================================================
# ARQUIVO 2: NiveisGammaPro (Linhas e Dashboard com Regime Visual)
# ==============================================================================
CODE_GAMMA = r"""
using System;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.IO;
using System.Windows.Media;
using System.Windows; 
using System.Xml.Serialization; 
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Tools;
using NinjaTrader.Gui.Chart;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;

namespace NinjaTrader.NinjaScript.Indicators
{
    public class NiveisGammaPro : Indicator
    {
        private DateTime ultimaLeitura = DateTime.MinValue;
        private string pastaGexData = @"C:\Users\alanb\Dropbox\Aplicativos\RoboGexNinjaV1"; 
        private double callWall=0, putWall=0, zeroGamma=0, posGex=0, negGex=0, maxPain=0, optionVolumeStrike=0;
        private double cw0DTE=0, pw0DTE=0, zg0DTE=0;
        private double cw1DTE=0, pw1DTE=0, zg1DTE=0;
        private double cw2DTE=0, pw2DTE=0, zg2DTE=0;
        private double cw7DTE=0, pw7DTE=0, zg7DTE=0;
        private bool niveisDisponiveis=false;
        private string cwMoney="$0", pwMoney="$0", optionVolume="0";
        private string dashRatio="0.00", dashNetFlow="Wait", dashNetGex="Wait", dashIv="0", dashIvSource="IV BASE";
        private string dashFlowVal="$0", dashGexVal="$0", dashRegime="Processando...";
        private string dashAlvoUp="0", dashAlvoDown="0";
        private string dashSource="";

        private System.Windows.Media.Brush brushCallLine, brushPutLine, brushVolumeLine;
        private System.Windows.Media.Brush brushCallText, brushPutText, brushVolumeText;
        private SimpleFont fonteDash, fonteLabels, fonteBold;

        [NinjaScriptProperty] [XmlIgnore] [Display(Name="Cor Call Wall", GroupName="Cores")] public System.Windows.Media.Brush CorCallWall { get; set; }
        [NinjaScriptProperty] [XmlIgnore] [Display(Name="Cor Put Wall", GroupName="Cores")] public System.Windows.Media.Brush CorPutWall { get; set; }
        [Browsable(false)] public string CorCallWallSerialize { get { return Serialize.BrushToString(CorCallWall); } set { CorCallWall = Serialize.StringToBrush(value); } }
        [Browsable(false)] public string CorPutWallSerialize { get { return Serialize.BrushToString(CorPutWall); } set { CorPutWall = Serialize.StringToBrush(value); } }

        protected override void OnStateChange() {
            if (State == State.SetDefaults) {
                Name = "NiveisGammaPro"; Calculate = Calculate.OnEachTick; IsOverlay = true; DisplayInDataBox = true; DrawOnPricePanel = true; ScaleJustification = NinjaTrader.Gui.Chart.ScaleJustification.Right;
                CorCallWall = Brushes.Cyan; CorPutWall = Brushes.Magenta; 
            }
        }

        protected override void OnBarUpdate() {
            if (DateTime.Now > ultimaLeitura.AddSeconds(3)) { LerArquivos(); CriarPinceis(); ultimaLeitura = DateTime.Now; ForceRefresh(); }
            Desenhar();
        }

        private void CriarPinceis() {
            if (brushCallLine == null && CorCallWall != null) { Color c = ((SolidColorBrush)CorCallWall).Color; brushCallLine = new SolidColorBrush(Color.FromArgb(50, c.R, c.G, c.B)); brushCallText = CorCallWall; }
            if (brushPutLine == null && CorPutWall != null) { Color c = ((SolidColorBrush)CorPutWall).Color; brushPutLine = new SolidColorBrush(Color.FromArgb(50, c.R, c.G, c.B)); brushPutText = CorPutWall; }
            if (brushVolumeLine == null) { brushVolumeLine = new SolidColorBrush(Color.FromArgb(80, 138, 43, 226)); brushVolumeText = Brushes.BlueViolet; }
            if (fonteDash == null) fonteDash = new SimpleFont("Consolas", 10) { Bold = true };
            if (fonteLabels == null) fonteLabels = new SimpleFont("Arial", 10);
            if (fonteBold == null) fonteBold = new SimpleFont("Arial", 11) { Bold = true };
            if(brushCallLine != null) brushCallLine.Freeze(); if(brushPutLine != null) brushPutLine.Freeze(); if(brushVolumeLine != null) brushVolumeLine.Freeze();
        }

        private void Desenhar() {
            DesenharNivelDte("CW0DTE", "0DTE CALL WALL", cw0DTE, Brushes.Yellow, DashStyleHelper.Dash, 3, 18);
            DesenharNivelDte("PW0DTE", "0DTE PUT WALL", pw0DTE, Brushes.DarkOrange, DashStyleHelper.Dash, 3, -18);
            DesenharNivelDte("CW1DTE", "1DTE CALL WALL", cw1DTE, Brushes.DodgerBlue, DashStyleHelper.Dash, 2, 30);
            DesenharNivelDte("PW1DTE", "1DTE PUT WALL", pw1DTE, Brushes.MediumPurple, DashStyleHelper.Dash, 2, -30);
            DesenharNivelDte("ZG1DTE", "1DTE GEX FLIP ESTIMADO", zg1DTE, Brushes.LightSkyBlue, DashStyleHelper.Dot, 2, 36);
            DesenharNivelDte("CW2DTE", "2DTE CALL WALL", cw2DTE, Brushes.Cyan, DashStyleHelper.Dash, 2, 42);
            DesenharNivelDte("PW2DTE", "2DTE PUT WALL", pw2DTE, Brushes.Magenta, DashStyleHelper.Dash, 2, -42);
            DesenharNivelDte("ZG2DTE", "2DTE GEX FLIP ESTIMADO", zg2DTE, Brushes.Goldenrod, DashStyleHelper.Dot, 2, 48);
            DesenharNivelDte("CW7DTE", "7DTE CALL WALL", cw7DTE, Brushes.LimeGreen, DashStyleHelper.Dash, 2, 54);
            DesenharNivelDte("PW7DTE", "7DTE PUT WALL", pw7DTE, Brushes.Tomato, DashStyleHelper.Dash, 2, -54);
            DesenharNivelDte("ZG7DTE", "7DTE GEX FLIP ESTIMADO", zg7DTE, Brushes.Silver, DashStyleHelper.Dot, 2, 60);
            if (callWall > 0 && brushCallLine != null) { Draw.HorizontalLine(this, "CW", callWall, brushCallLine, DashStyleHelper.Solid, 5); Draw.Text(this, "TxtCW", false, "CALL WALL | " + cwMoney + " | " + callWall, -10, callWall, 18, brushCallText, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100); }
            else { RemoveDrawObject("CW"); RemoveDrawObject("TxtCW"); }
            if (putWall > 0 && brushPutLine != null) { Draw.HorizontalLine(this, "PW", putWall, brushPutLine, DashStyleHelper.Solid, 5); Draw.Text(this, "TxtPW", false, "PUT WALL | " + pwMoney + " | " + putWall, -10, putWall, -18, brushPutText, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100); }
            else { RemoveDrawObject("PW"); RemoveDrawObject("TxtPW"); }
            if (optionVolumeStrike > 0 && brushVolumeLine != null) { Draw.HorizontalLine(this, "DP", optionVolumeStrike, brushVolumeLine, DashStyleHelper.Solid, 6); Draw.Text(this, "TxtDP", false, "MAX OPTION VOLUME | " + optionVolume + " contracts [" + optionVolumeStrike + "]", -10, optionVolumeStrike, 35, brushVolumeText, fonteBold, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100); }
            else { RemoveDrawObject("DP"); RemoveDrawObject("TxtDP"); }
            if (zeroGamma > 0) { Draw.HorizontalLine(this, "ZG", zeroGamma, Brushes.White, DashStyleHelper.Dot, 1); Draw.Text(this, "TxtZG", false, "GEX FLIP ESTIMADO [" + zeroGamma + "]", -60, zeroGamma, 10, Brushes.White, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100); }
            else { RemoveDrawObject("ZG"); RemoveDrawObject("TxtZG"); }
            if (maxPain > 0) { Draw.HorizontalLine(this, "MP", maxPain, Brushes.Goldenrod, DashStyleHelper.Dash, 2); Draw.Text(this, "TxtMP", false, "MAX PAIN [" + maxPain + "]", -60, maxPain, -10, Brushes.Goldenrod, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100); }
            else { RemoveDrawObject("MP"); RemoveDrawObject("TxtMP"); }

            Brush corFundoDash = Brushes.Black;
            Brush corTextoRegime = Brushes.White;
            
            if (dashRegime.Contains("SHORT")) { corFundoDash = Brushes.DarkRed; corTextoRegime = Brushes.Yellow; }
            else if (dashRegime.Contains("LONG")) { corFundoDash = Brushes.DarkGreen; corTextoRegime = Brushes.White; }

            string titulo = "🛡️ QUANT ENGINE V8\n------------------";
            string fonte = string.IsNullOrEmpty(dashSource) ? "" : "\nFONTE: " + dashSource;
            string flipStatus = !niveisDisponiveis
                ? "GEX: arquivo de niveis indisponivel"
                : zeroGamma > 0
                    ? "GEX FLIP estimado: " + zeroGamma
                    : "GEX FLIP: sem cruzamento na faixa";
            double ratioNum = 0;
            double.TryParse(dashRatio, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out ratioNum);
            string ratioTag = ratioNum > 1.20 ? "[PUT DOMINANT]" : (ratioNum > 0 && ratioNum < 0.80 ? "[CALL DOMINANT]" : "[NEUTRAL]");
            string niveisResumo = "\nPOS GEX (CW): " + callWall + " (" + cwMoney + ") | NEG GEX (PW): " + putWall + " (" + pwMoney + ")"
                + "\nMAX PAIN: " + maxPain + " | BLOCK/MAX VOL: " + optionVolumeStrike + " (" + optionVolume + " ctrs)";
            string alvosResumo = (dashAlvoUp != "0" && dashAlvoDown != "0") ? "\nALVOS VOL: " + dashAlvoDown + " <-> " + dashAlvoUp : "";
            string ivLabel = string.IsNullOrWhiteSpace(dashIvSource) ? "IV BASE" : dashIvSource.ToUpperInvariant();
            string dados = "\nREGIME: " + dashRegime + "\n------------------" + "\nCALL/PUT VOLUME BALANCE (source/model units): " + dashNetFlow + " (" + dashFlowVal + ")" + "\nNET GEX (estimado): " + dashNetGex + " (" + dashGexVal + ")" + niveisResumo + "\n" + flipStatus + "\nRATIO: " + dashRatio + " " + ratioTag + "\n" + ivLabel + ": " + dashIv + "%" + alvosResumo + fonte + "\nATUALIZADO: " + DateTime.Now.ToString("HH:mm:ss");
            Draw.TextFixed(this, "DashFundo", titulo + dados, TextPosition.TopLeft, corTextoRegime, fonteDash, corFundoDash, Brushes.Black, 100);
        }

        private void DesenharNivelDte(string tag, string label, double value, System.Windows.Media.Brush brush, DashStyleHelper dash, int width, int yOffset) {
            string textTag = "Txt" + tag;
            if (value > 0) {
                Draw.HorizontalLine(this, tag, value, brush, dash, width);
                Draw.Text(this, textTag, false, label + " [" + value + "]", -10, value, yOffset, brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);
            } else {
                RemoveDrawObject(tag);
                RemoveDrawObject(textTag);
            }
        }

        private void LerArquivos() {
            try {
                dashSource = "";
                niveisDisponiveis=false;
                callWall=0; putWall=0; zeroGamma=0; posGex=0; negGex=0; maxPain=0; optionVolumeStrike=0;
                cw0DTE=0; pw0DTE=0; zg0DTE=0;
                cw1DTE=0; pw1DTE=0; zg1DTE=0;
                cw2DTE=0; pw2DTE=0; zg2DTE=0;
                cw7DTE=0; pw7DTE=0; zg7DTE=0;
                cwMoney="$0"; pwMoney="$0"; optionVolume="0";
                dashRatio="0.00"; dashNetFlow="Wait"; dashNetGex="Wait";
                dashIv="0"; dashIvSource="IV BASE"; dashFlowVal="0"; dashGexVal="0";
                dashAlvoUp="0"; dashAlvoDown="0";
                dashRegime="Processando...";
                if (Instrument == null) return; string s = Instrument.MasterInstrument.Name;
                if(s.Contains("ES"))s="ES"; 
                else if(s.Contains("NQ"))s="NQ"; 
                else if(s.Contains("GC"))s="GC"; 
                else if(s.Contains("CL"))s="CL"; 
                else if(s.Contains("ZB"))s="ZB"; 
                else if(s.Contains("ZN"))s="ZN";
                else if(s.Contains("YM"))s="YM";
                else if(s.Contains("RTY") || s.Contains("M2K"))s="RTY";
                else if(s.Contains("NG") || s.Contains("QG"))s="NG";

                string f1 = Path.Combine(pastaGexData, "NiveisGamma_" + s + ".csv");
                if (File.Exists(f1)) {
                    var p = File.ReadAllText(f1).Split(',');
                    dashSource = p.Length >= 10 ? p[9].Trim() : "";
                    if (p.Length >= 7) {
                        bool callParsed = double.TryParse(p[0], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out callWall);
                        bool putParsed = double.TryParse(p[1], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out putWall);
                        bool flipParsed = string.IsNullOrWhiteSpace(p[2]) ||
                            double.TryParse(p[2], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out zeroGamma);
                        double.TryParse(p[3], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out posGex);
                        double.TryParse(p[4], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out negGex);
                        niveisDisponiveis = callParsed && putParsed && flipParsed;
                        if (!niveisDisponiveis) Print("NiveisGammaPro: CSV de niveis invalido para " + s + ".");
                        cwMoney = p[5]; pwMoney = p[6];
                    }
                    if (p.Length >= 9) {
                        double.TryParse(p[7], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out cw0DTE);
                        double.TryParse(p[8], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out pw0DTE);
                    }
                }
                if (cw0DTE == 0 && pw0DTE == 0) {
                    LerNiveisDte(s, "0DTE", out cw0DTE, out pw0DTE, out zg0DTE);
                }
                LerNiveisDte(s, "1DTE", out cw1DTE, out pw1DTE, out zg1DTE);
                LerNiveisDte(s, "2DTE", out cw2DTE, out pw2DTE, out zg2DTE);
                LerNiveisDte(s, "7DTE", out cw7DTE, out pw7DTE, out zg7DTE);
                string f2 = Path.Combine(pastaGexData, "AlvosVolatilidade_" + s + ".csv");
                if (File.Exists(f2)) { 
                    var p = File.ReadAllText(f2).Split(','); 
                    if (p.Length >= 9) { 
                        double.TryParse(p[0], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out maxPain); 
                        double.TryParse(p[1], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out optionVolumeStrike); 
                        dashRatio = p[2]; dashIv = p[3]; dashNetFlow = p[4]; dashNetGex = p[5]; optionVolume = p[6]; dashFlowVal = p[7]; dashGexVal = p[8]; 
                    }
                    if (p.Length >= 11) {
                        dashAlvoUp = p[9].Trim(); dashAlvoDown = p[10].Trim();
                    }
                    if (p.Length >= 12) {
                        dashRegime = p[11];
                    }
                    if (p.Length >= 13 && !string.IsNullOrWhiteSpace(p[12])) {
                        dashIvSource = p[12].Trim();
                    }
                }
            } catch (Exception ex) { niveisDisponiveis=false; Print("NiveisGammaPro: falha ao ler CSV GEX: " + ex.Message); }
        }

        private void LerNiveisDte(string symbol, string dte, out double call, out double put, out double zero) {
            call=0; put=0; zero=0;
            string path = Path.Combine(pastaGexData, "NiveisGamma_" + symbol + "_" + dte + ".csv");
            if (!File.Exists(path)) return;
            string[] values = File.ReadAllText(path).Split(',');
            if (values.Length < 3) return;
            double.TryParse(values[0], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out call);
            double.TryParse(values[1], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out put);
            double.TryParse(values[2], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out zero);
        }
    }
}
"""

# ==============================================================================
# ARQUIVO 3: MoneyRiskPro V76 (AVANÇADO) - Fonte: MoneyRiskProAvançado.py
# ==============================================================================
CODE_RISK_V76 = r"""
using System;
using System.IO;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Windows; 
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;

public enum RiskModeV76 
{ 
    Institucional_Smart, 
    Apenas_ATR, 
    Manual_Fixo 
}

namespace NinjaTrader.NinjaScript.Indicators
{
    public class MoneyRiskPro : Indicator
    {
        [NinjaScriptProperty] [Display(Name="Risco Max por Trade ($)", Order=1, GroupName="1. Financeiro")] 
        public double RiscoMax { get; set; }
        
        [NinjaScriptProperty] [Display(Name="Modo de Operação", Order=2, GroupName="2. Estratégia")] 
        public RiskModeV76 ModoCalculo { get; set; }
        
        [NinjaScriptProperty] [Display(Name="Fator Sensibilidade IV", Order=3, GroupName="2. Estratégia")] 
        public double FatorIV { get; set; }
        
        [NinjaScriptProperty] [Display(Name="Periodo ATR (Backup)", Order=4, GroupName="2. Estratégia")] 
        public int PeriodoATR { get; set; }
        
        [NinjaScriptProperty] [Display(Name="Multiplicador ATR", Order=5, GroupName="2. Estratégia")] 
        public double MultiplicadorATR { get; set; }

        [NinjaScriptProperty] [Display(Name="Stop Fixo (Ticks)", Order=6, GroupName="2. Estratégia")] 
        public int StopTicksFixo { get; set; }

        [NinjaScriptProperty] [Display(Name="Mostrar Linhas", Order=7, GroupName="3. Visual")] 
        public bool ShowLines { get; set; }

        private SimpleFont ft1, ft2;
        private double currentIV = 0;
        private string currentIVSource = "IV base assumida";
        private string currentRegime = "Neutro";
        private double dailyExpectedMove = 0;
        private string pastaGexData = @"C:\Users\alanb\Dropbox\Aplicativos\RoboGexNinjaV1";
        private DateTime ultimaLeitura = DateTime.MinValue;
        private ATR indicadorATR; 

        protected override void OnStateChange() {
            if(State==State.SetDefaults){ 
                Name="MoneyRiskPro"; 
                Description="Versão V76 - Risco Institucional Avançado";
                Calculate = Calculate.OnBarClose; 
                IsOverlay=true; 
                DisplayInDataBox=true; 
                DrawOnPricePanel=true; 
                
                RiscoMax = 250; 
                ModoCalculo = RiskModeV76.Institucional_Smart; 
                FatorIV = 0.15; 
                PeriodoATR = 14; 
                MultiplicadorATR = 2.0; 
                StopTicksFixo = 20; 
                ShowLines = true;
            }
            else if (State == State.DataLoaded)
            {
                indicadorATR = ATR(PeriodoATR);
            }
        }

        protected override void OnBarUpdate() {
            if (CurrentBar < PeriodoATR || !ShowLines) return;

            if (ModoCalculo == RiskModeV76.Institucional_Smart && DateTime.Now > ultimaLeitura.AddSeconds(5)) {
                LerDadosCSV();
                ultimaLeitura = DateTime.Now;
            }

            if (currentRegime.Contains("SHORT")) {
                BackBrush = new SolidColorBrush(Color.FromArgb(6, 255, 0, 0));
            } else if (currentRegime.Contains("LONG")) {
                BackBrush = new SolidColorBrush(Color.FromArgb(6, 0, 255, 0));
            } else {
                BackBrush = null;
            }

            double p = Close[0];
            double tickVal = TickSize;
            double stopDistance = 0;
            int ticksCalculados = 0;
            string statusMsg = "";
            Brush bgStatus = Brushes.DarkSlateBlue;
            
            bool usarIV = (ModoCalculo == RiskModeV76.Institucional_Smart && currentIV > 0);
            bool usarATR = (ModoCalculo == RiskModeV76.Apenas_ATR) || (ModoCalculo == RiskModeV76.Institucional_Smart && currentIV == 0);
            
            if (usarIV)
            {
                dailyExpectedMove = p * (currentIV / 1600.0);
                stopDistance = dailyExpectedMove * FatorIV;
                if (stopDistance < 5 * tickVal) stopDistance = 5 * tickVal;
                statusMsg = currentIVSource + ": " + currentIV + "% (Amp: " + dailyExpectedMove.ToString("F0") + ")";
                bgStatus = Brushes.DarkGreen; 
            }
            else if (usarATR)
            {
                double valorATR = indicadorATR[0];
                stopDistance = valorATR * MultiplicadorATR;
                statusMsg = (ModoCalculo == RiskModeV76.Institucional_Smart) ? "⚠️ IV OFF (Usando ATR)" : "Modo ATR";
                if (ModoCalculo == RiskModeV76.Institucional_Smart) bgStatus = Brushes.DarkOrange; 
            }
            else
            {
                stopDistance = StopTicksFixo * tickVal;
                statusMsg = "Manual Fixo";
                bgStatus = Brushes.Gray;
            }

            ticksCalculados = (int)Math.Round(stopDistance / tickVal);
            if(ticksCalculados < 4) ticksCalculados = 4;

            double stopPrice = p - stopDistance;
            double alvo1 = p + (stopDistance * 1.0);
            double alvo2 = p + (stopDistance * 2.0);
            double alvo3 = p + (stopDistance * 3.0);

            if(ft2 == null) ft2 = new SimpleFont("Consolas", 9);

            Draw.Line(this, "StopL", false, 0, stopPrice, -5, stopPrice, Brushes.Red, DashStyleHelper.Dot, 2);
            Draw.Text(this, "TxtStop", false, "STOP [" + ticksCalculados + "t]", 0, stopPrice, 10, Brushes.Red, ft2, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);

            Draw.Line(this, "Alvo1", false, 0, alvo1, -3, alvo1, Brushes.LightGreen, DashStyleHelper.Dot, 1);
            Draw.Line(this, "Alvo2", false, 0, alvo2, -4, alvo2, Brushes.LimeGreen, DashStyleHelper.Dash, 2);
            Draw.Text(this, "TxtA2", false, "2:1", 0, alvo2, -10, Brushes.LimeGreen, ft2, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);

            double valorPorTick = Instrument.MasterInstrument.PointValue * tickVal;
            if(valorPorTick == 0) valorPorTick = 1;
            
            int lotesCalc = 0;
            if (ticksCalculados > 0)
                lotesCalc = (int)(RiscoMax / (ticksCalculados * valorPorTick));

            if(ft1==null) ft1 = new SimpleFont("Arial", 10){Bold=true};

            string t = "🛡️ RISK V76 (GLOBAL)\n-----------------------";
            string tDados = "\n" + statusMsg;
            string tLote = "\n👉 LOTE: " + lotesCalc + " ctrs";
            
            if(lotesCalc == 0) { bgStatus = Brushes.Red; tLote = "\n⛔ RISCO MUITO ALTO"; }

            Draw.TextFixed(this, "RiskBox", t + tDados + tLote, TextPosition.BottomRight, Brushes.White, ft2, bgStatus, Brushes.Black, 100);
        }

        private void LerDadosCSV() {
            currentIV = 0; 
            currentRegime = "Neutro";
            try {
                if(Instrument==null)return;
                string s = Instrument.MasterInstrument.Name;
                if(s.Contains("ES"))s="ES"; 
                else if(s.Contains("NQ"))s="NQ"; 
                else if(s.Contains("GC"))s="GC"; 
                else if(s.Contains("CL"))s="CL"; 
                else if(s.Contains("ZB"))s="ZB"; 
                else if(s.Contains("ZN"))s="ZN";
                else if(s.Contains("YM"))s="YM";
                else if(s.Contains("RTY") || s.Contains("M2K"))s="RTY";
                else if(s.Contains("NG") || s.Contains("QG"))s="NG";

                string f = Path.Combine(pastaGexData, "AlvosVolatilidade_"+s+".csv");
                if(File.Exists(f)) { 
                    var lines = File.ReadAllText(f).Split(','); 
                    if(lines.Length >= 4) { 
                        string ivString = lines[3].Replace("%", "").Trim();
                        double.TryParse(ivString, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out currentIV);
                    }
                    if(lines.Length >= 12) {
                        currentRegime = lines[11].Trim();
                    }
                    if(lines.Length >= 13 && !string.IsNullOrWhiteSpace(lines[12])) {
                        currentIVSource = lines[12].Trim();
                    }
                }
            } catch {}
        }
    }
}
"""

# ==============================================================================
# ARQUIVO 4: DailyOHLCPro (Gold V65) - Fonte: DAILYOLHC.PY
# ==============================================================================
CODE_OHLC = r"""
using System;
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
    public class DailyOHLCPro : Indicator
    {
        private double pdOpen, pdHigh, pdLow, pdClose;
        private SimpleFont fonteLabels;

        [NinjaScriptProperty] [XmlIgnore] [Display(Name="Cor da Faixa RTH", Order=1, GroupName="Visual")]
        public Brush CorFundo { get; set; }

        [Browsable(false)] public string CorFundoSerialize
        { get { return Serialize.BrushToString(CorFundo); } set { CorFundo = Serialize.StringToBrush(value); } }

        [NinjaScriptProperty] [Display(Name="Opacidade", Order=2, GroupName="Visual")]
        public int Opacidade { get; set; }

        [NinjaScriptProperty] [Display(Name="Inicio RTH (Hora)", Order=3, GroupName="Sessao")] public int HoraInicio { get; set; }
        [NinjaScriptProperty] [Display(Name="Fim RTH (Hora)", Order=4, GroupName="Sessao")] public int HoraFim { get; set; }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "RTH Vertical Strip (Gold V65)";
                Name = "DailyOHLCPro";
                Calculate = Calculate.OnBarClose;
                IsOverlay = true;
                DrawOnPricePanel = true;
                
                CorFundo = Brushes.DarkSlateBlue; 
                Opacidade = 25; 
                HoraInicio = 930;  
                HoraFim = 1615;    

                AddPlot(new Stroke(Brushes.LimeGreen, DashStyleHelper.Solid, 2), PlotStyle.Line, "Prev High");
                AddPlot(new Stroke(Brushes.Red, DashStyleHelper.Solid, 2), PlotStyle.Line, "Prev Low");
                AddPlot(new Stroke(Brushes.Goldenrod, DashStyleHelper.Solid, 2), PlotStyle.Line, "Prev Close");
                AddPlot(new Stroke(Brushes.DodgerBlue, DashStyleHelper.Dash, 1), PlotStyle.Line, "Prev Open");
            }
            else if (State == State.Configure) { AddDataSeries(BarsPeriodType.Day, 1); }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBars[0] < 1 || CurrentBars[1] < 1) return;

            if (BarsInProgress == 1) { pdOpen = Opens[1][0]; pdHigh = Highs[1][0]; pdLow = Lows[1][0]; pdClose = Closes[1][0]; }

            if (BarsInProgress == 0 && pdHigh > 0)
            {
                Values[0][0] = pdHigh; Values[1][0] = pdLow; Values[2][0] = pdClose; Values[3][0] = pdOpen;

                DateTime agora = Time[0];
                DateTime dataBase = agora.Date;
                DateTime inicioRTH = dataBase.AddHours(HoraInicio / 100).AddMinutes(HoraInicio % 100);
                DateTime fimRTH = dataBase.AddHours(HoraFim / 100).AddMinutes(HoraFim % 100);

                if (agora >= inicioRTH)
                {
                    Draw.Rectangle(this, "RTH_Strip_" + dataBase.ToString("yyyyMMdd"), false, 
                        inicioRTH, 100000, fimRTH, 0, 
                        Brushes.Transparent, CorFundo, Opacidade);
                }

                if (fonteLabels == null) fonteLabels = new SimpleFont("Arial", 9);
                Draw.Text(this, "TxtHigh", false, "PREV HIGH", 0, pdHigh, 10, Brushes.LimeGreen, fonteLabels, TextAlignment.Left, Brushes.Transparent, Brushes.Transparent, 100);
                Draw.Text(this, "TxtLow", false, "PREV LOW", 0, pdLow, -10, Brushes.Red, fonteLabels, TextAlignment.Left, Brushes.Transparent, Brushes.Transparent, 100);
                Draw.Text(this, "TxtClose", false, "PREV CLOSE", 0, pdClose, 10, Brushes.Goldenrod, fonteLabels, TextAlignment.Left, Brushes.Transparent, Brushes.Transparent, 100);
                Draw.Text(this, "TxtOpen", false, "PREV OPEN", 0, pdOpen, -10, Brushes.DodgerBlue, fonteLabels, TextAlignment.Left, Brushes.Transparent, Brushes.Transparent, 100);
            }
        }
    }
}
"""

# ==============================================================================
# ARQUIVO 5: GlobexRangePro (Gold V65) - Fonte: DAILYOLHC.PY
# ==============================================================================
CODE_GLOBEX = r"""
using System;
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
    public class GlobexRangePro : Indicator
    {
        private double globexHigh = double.MinValue;
        private double globexLow = double.MaxValue;
        private DateTime sessionStart;
        private bool inSession = false;
        private SimpleFont fonteGlobex;

        [NinjaScriptProperty] [XmlIgnore] [Display(Name="Cor das Linhas", Order=1, GroupName="Visual")]
        public Brush CorLinhas { get; set; }

        [Browsable(false)] public string CorLinhasSerialize
        { get { return Serialize.BrushToString(CorLinhas); } set { CorLinhas = Serialize.StringToBrush(value); } }

        [NinjaScriptProperty] [Display(Name="Inicio (18:00)", Order=3, GroupName="Horarios")]
        public int HoraInicio { get; set; }

        [NinjaScriptProperty] [Display(Name="Fim (09:30)", Order=4, GroupName="Horarios")]
        public int HoraFim { get; set; }

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Globex Strategy (Lines Only)";
                Name = "GlobexRangePro";
                Calculate = Calculate.OnBarClose;
                IsOverlay = true;
                DrawOnPricePanel = true;

                CorLinhas = Brushes.Silver;
                HoraInicio = 1800; 
                HoraFim = 930;     
            }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < 1) return;

            int t = ToTime(Time[0]);
            
            if (t >= HoraInicio && ToTime(Time[1]) < HoraInicio) 
            {
                globexHigh = High[0]; globexLow = Low[0]; sessionStart = Time[0]; inSession = true;
            }
            
            bool isOvernight = (t >= HoraInicio) || (t < HoraFim);
            
            if (inSession && isOvernight)
            {
                if (High[0] > globexHigh) globexHigh = High[0];
                if (Low[0] < globexLow) globexLow = Low[0];
                
                string tag = "Globex_" + sessionStart.ToString("MMdd");
                Draw.Line(this, "LineH_" + tag, false, sessionStart, globexHigh, Time[0], globexHigh, CorLinhas, DashStyleHelper.Dash, 1);
                Draw.Line(this, "LineL_" + tag, false, sessionStart, globexLow, Time[0], globexLow, CorLinhas, DashStyleHelper.Dash, 1);
            }
            
            if (inSession && t >= HoraFim && ToTime(Time[1]) < HoraFim)
            {
                inSession = false; 
                string tag = "Globex_" + sessionStart.ToString("MMdd");
                DateTime fimDoDia = Time[0].Date.AddHours(17); 

                Draw.Line(this, "LineH_" + tag, false, sessionStart, globexHigh, fimDoDia, globexHigh, CorLinhas, DashStyleHelper.Dash, 2);
                Draw.Line(this, "LineL_" + tag, false, sessionStart, globexLow, fimDoDia, globexLow, CorLinhas, DashStyleHelper.Dash, 2);
                
                if(fonteGlobex == null) fonteGlobex = new SimpleFont("Arial", 9);
                Draw.Text(this, "TxtH_" + tag, false, "GLOBEX H", Time[0], globexHigh, 10, CorLinhas, fonteGlobex, TextAlignment.Left, Brushes.Transparent, Brushes.Transparent, 100);
                Draw.Text(this, "TxtL_" + tag, false, "GLOBEX L", Time[0], globexLow, -10, CorLinhas, fonteGlobex, TextAlignment.Left, Brushes.Transparent, Brushes.Transparent, 100);
            }
        }
    }
}
"""

# ==============================================================================
# ARQUIVO 6: VolatilidadeImplicitaPro (Bandas 1, 2 e 3 SD da IV)
# ==============================================================================
CODE_VOLATILIDADE = r"""
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
        [Display(Name="Linha DOWN (-95%)", Order=2, GroupName="2. Visual: Bandas 2 SD")]
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
                double dem = p * (currentIV / 1600.0); 

                double up1 = p + dem;
                double dn1 = p - dem;
                double up2 = p + (dem * 2);
                double dn2 = p - (dem * 2);
                double up3 = p + (dem * 3);
                double dn3 = p - (dem * 3);

                Draw.HorizontalLine(this, "UP1", up1, LinhaUp1.Brush, LinhaUp1.DashStyleHelper, (int)LinhaUp1.Width);
                Draw.Text(this, "TxtUP1", false, "1 SD (+68%) [" + up1.ToString("F2") + "]", -10, up1, 10, LinhaUp1.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);
                
                Draw.HorizontalLine(this, "DN1", dn1, LinhaDn1.Brush, LinhaDn1.DashStyleHelper, (int)LinhaDn1.Width);
                Draw.Text(this, "TxtDN1", false, "-1 SD (-68%) [" + dn1.ToString("F2") + "]", -10, dn1, -10, LinhaDn1.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);

                Draw.HorizontalLine(this, "UP2", up2, LinhaUp2.Brush, LinhaUp2.DashStyleHelper, (int)LinhaUp2.Width);
                Draw.Text(this, "TxtUP2", false, "2 SD (+95%) [" + up2.ToString("F2") + "]", -10, up2, 10, LinhaUp2.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);
                
                Draw.HorizontalLine(this, "DN2", dn2, LinhaDn2.Brush, LinhaDn2.DashStyleHelper, (int)LinhaDn2.Width);
                Draw.Text(this, "TxtDN2", false, "-2 SD (-95%) [" + dn2.ToString("F2") + "]", -10, dn2, -10, LinhaDn2.Brush, fonteLabels, TextAlignment.Right, Brushes.Transparent, Brushes.Transparent, 100);

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
"""

# ==============================================================================
# ARQUIVO 7: FluentliExpectedMove (Nuvens de Expected Move Topo/Fundo)
# ==============================================================================
CODE_EXPECTED_MOVE = r'''
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
'''

# ==============================================================================
# ESCREVENDO TUDO NO DISCO
# ==============================================================================
arquivos_para_instalar = {
    "NiveisEstruturaPro.cs": CODE_ESTRUTURA,
    "NiveisGammaPro.cs": CODE_GAMMA,
    "MoneyRiskPro.cs": CODE_RISK_V76,
    "DailyOHLCPro.cs": CODE_OHLC,
    "GlobexRangePro.cs": CODE_GLOBEX,
    "VolatilidadeImplicitaPro.cs": CODE_VOLATILIDADE,
    "FluentliExpectedMove.cs": CODE_EXPECTED_MOVE
}

print("\n--- INICIANDO GRAVAÇÃO ---")
try:
    for nome_arquivo, conteudo in arquivos_para_instalar.items():
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)
        
        if os.path.exists(caminho_completo):
            try:
                os.remove(caminho_completo)
            except:
                pass 
                
        with open(caminho_completo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        print(f"✅ SUCESSO: {nome_arquivo} atualizado para versão PREMIUM.")

    messagebox.showinfo("Instalação MESTRE Concluída", 
                        "✅ SUCESSO TOTAL!\n\n"
                        f"Foram instalados {len(arquivos_para_instalar)} Indicadores:\n"
                        "1. NiveisEstruturaPro (Gamma Histograma)\n"
                        "2. NiveisGammaPro (Linhas e Dashboard)\n"
                        "3. MoneyRiskPro (Versão V76 - ATR Inteligente)\n"
                        "4. DailyOHLCPro (Faixa Vertical RTH)\n"
                        "5. GlobexRangePro (Apenas Linhas)\n"
                        "6. VolatilidadeImplicitaPro (Bandas 1, 2 e 3 SD da IV)\n"
                        "7. FluentliExpectedMove (Nuvens de Expected Move)\n\n"
                        "👉 AGORA: Abra o NinjaTrader e aperte F5 (ou reinicie).")

except Exception as e:
    messagebox.showerror("Erro Fatal", f"Não foi possível gravar os arquivos:\n{e}")