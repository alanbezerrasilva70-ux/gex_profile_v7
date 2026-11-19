import os
import shutil
import tkinter.messagebox as messagebox

MARCA_PASTA = "VeltrixQuant"
DASHBOARD_URL_PADRAO = os.environ.get("VELTRIX_DASHBOARD_URL", "https://gex-dashboard-git-master-gex-cloud.vercel.app").strip() or "https://gex-dashboard-git-master-gex-cloud.vercel.app"

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
# ARQUIVO 1: NiveisEstruturaPro (Histograma Gamma) - SharpDX Neon Glow Ultra-Leve
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
        public class GammaLevel {
            public double Strike;
            public double NetGamma;
            public double CallOI;
            public double PutOI;
            public double CallVol;
            public double PutVol;
            public string Label;
            public bool IsNewMoney;
        }
        private List<GammaLevel> niveisGamma = new List<GammaLevel>();
        private DateTime ultimaLeitura = DateTime.MinValue;
        private string pastaGexData = @"C:\Users\alanb\Dropbox\Dropbox\Aplicativos\RoboGexNinjaV1";

        private SharpDX.DirectWrite.Factory dxFactory;
        private SharpDX.DirectWrite.TextFormat dxTextFormat, dxTextFormatBold;
        private SharpDX.Direct2D1.SolidColorBrush dxBrushCall, dxBrushPut;
        private SharpDX.Direct2D1.SolidColorBrush dxBrushCallGlow, dxBrushPutGlow, dxBrushCallGlowOuter, dxBrushPutGlowOuter;
        private SharpDX.Direct2D1.SolidColorBrush dxBrushCallTip, dxBrushPutTip, dxBrushSpecular;
        private SharpDX.Direct2D1.SolidColorBrush dxBrushText, dxBrushHighlight, dxBrushNewMoney, dxBrushLabelBg, dxBrushLabelBorder, dxBrushLeader;
        private SharpDX.Direct2D1.GradientStopCollection dxStopsCall, dxStopsPut, dxStopsCallHeavy, dxStopsPutHeavy;
        private SharpDX.Direct2D1.LinearGradientBrush dxGradCall, dxGradPut, dxGradCallHeavy, dxGradPutHeavy;

        private float cachedCanvasRight = -1f;
        private int cachedLarguraMax = -1;
        private int cachedOpacidade = -1;
        private string ultimaAssinaturaCsv = "";
        private readonly List<SharpDX.RectangleF> usedTagRects = new List<SharpDX.RectangleF>(64);

        [NinjaScriptProperty] [Display(Name="Opacidade (%)", Order=1, GroupName="Visual")] public int Opacidade { get; set; }
        [NinjaScriptProperty] [Display(Name="Largura Max", Order=2, GroupName="Visual")] public int LarguraMax { get; set; }
        [NinjaScriptProperty] [Display(Name="Vencimento DTE (ALL, 0DTE, 1DTE, 2DTE, 7DTE)", Order=3, GroupName="Visual")] public string VencimentoDTE { get; set; }
        [NinjaScriptProperty] [Display(Name="Modo Histograma (GAMMA, VOLUME, OPENING_FLOW)", Order=4, GroupName="Visual")] public string ModoHistograma { get; set; }
        [NinjaScriptProperty] [Display(Name="Efeito Visual (NEON_GLOW, GLASS_3D, ECO)", Order=5, GroupName="Visual")] public string EfeitoVisual { get; set; }
        [NinjaScriptProperty] [Display(Name="Espessura Max Barra (px)", Order=6, GroupName="Visual")] public int EspessuraMax { get; set; }

        protected override void OnStateChange() {
            if (State == State.SetDefaults) {
                Name = "VeltrixQuant - NiveisEstruturaPro"; Calculate = Calculate.OnEachTick; IsOverlay = true;
                Opacidade = 58; LarguraMax = 300; VencimentoDTE = "ALL"; ModoHistograma = "GAMMA";
                EfeitoVisual = "NEON_GLOW"; EspessuraMax = 10;
            } else if (State == State.DataLoaded) {
                LerTudo();
            } else if (State == State.Terminated) {
                LimparRecursos();
            }
        }

        protected override void OnBarUpdate() {
            if (DateTime.Now > ultimaLeitura.AddSeconds(5)) {
                ultimaLeitura = DateTime.Now;
                if (LerTudo()) ForceRefresh();
            }
        }

        private double ObterValorMetrica(GammaLevel n, string modo) {
            if (modo == "VOLUME") return n.CallVol - n.PutVol;
            if (modo == "OPENING_FLOW" || modo == "NEW_MONEY") {
                double newCall = Math.Max(0, n.CallVol - n.CallOI);
                double newPut = Math.Max(0, n.PutVol - n.PutOI);
                return newCall - newPut;
            }
            return n.NetGamma;
        }

        private void EnsureStaticResources(int safeOpacity) {
            if (dxFactory == null) dxFactory = new SharpDX.DirectWrite.Factory();
            if (dxTextFormat == null) dxTextFormat = new TextFormat(dxFactory, "Consolas", SharpDX.DirectWrite.FontWeight.SemiBold, SharpDX.DirectWrite.FontStyle.Normal, 10f);
            if (dxTextFormatBold == null) dxTextFormatBold = new TextFormat(dxFactory, "Consolas", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 10.5f);

            if (dxBrushCallTip == null) dxBrushCallTip = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.22f, 0.98f, 0.85f, 1.0f));
            if (dxBrushPutTip == null) dxBrushPutTip = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1.00f, 0.32f, 0.62f, 1.0f));
            if (dxBrushCallGlow == null) dxBrushCallGlow = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.08f, 0.88f, 0.65f, 0.18f));
            if (dxBrushPutGlow == null) dxBrushPutGlow = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.98f, 0.22f, 0.45f, 0.19f));
            if (dxBrushCallGlowOuter == null) dxBrushCallGlowOuter = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.06f, 0.82f, 0.60f, 0.08f));
            if (dxBrushPutGlowOuter == null) dxBrushPutGlowOuter = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.96f, 0.18f, 0.42f, 0.08f));
            if (dxBrushSpecular == null) dxBrushSpecular = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1.0f, 1.0f, 1.0f, 0.26f));
            if (dxBrushText == null) dxBrushText = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.94f, 0.97f, 1.0f, 1.0f));
            if (dxBrushHighlight == null) dxBrushHighlight = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1.0f, 0.88f, 0.28f, 0.95f));
            if (dxBrushNewMoney == null) dxBrushNewMoney = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(1.0f, 0.68f, 0.12f, 0.98f));
            if (dxBrushLabelBg == null) dxBrushLabelBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.03f, 0.05f, 0.09f, 0.90f));
            if (dxBrushLabelBorder == null) dxBrushLabelBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.24f, 0.32f, 0.45f, 0.70f));
            if (dxBrushLeader == null) dxBrushLeader = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.60f, 0.70f, 0.85f, 0.45f));

            if (cachedOpacidade != safeOpacity || dxGradCall == null) {
                DisporBrushesDinamicos();
                float baseA = Math.Max(0.15f, Math.Min(1.0f, safeOpacity / 100f));
                dxBrushCall = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.06f, 0.78f, 0.56f, Math.Min(0.95f, baseA * 1.1f)));
                dxBrushPut = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new Color4(0.94f, 0.24f, 0.42f, Math.Min(0.95f, baseA * 1.1f)));

                dxStopsCall = new SharpDX.Direct2D1.GradientStopCollection(RenderTarget, new SharpDX.Direct2D1.GradientStop[] {
                    new SharpDX.Direct2D1.GradientStop { Position = 0.00f, Color = new Color4(0.02f, 0.28f, 0.22f, baseA * 0.52f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 0.58f, Color = new Color4(0.06f, 0.76f, 0.54f, Math.Min(0.92f, baseA * 1.18f)) },
                    new SharpDX.Direct2D1.GradientStop { Position = 1.00f, Color = new Color4(0.18f, 0.94f, 0.80f, Math.Min(0.98f, baseA * 1.38f)) }
                });
                dxStopsCallHeavy = new SharpDX.Direct2D1.GradientStopCollection(RenderTarget, new SharpDX.Direct2D1.GradientStop[] {
                    new SharpDX.Direct2D1.GradientStop { Position = 0.00f, Color = new Color4(0.03f, 0.36f, 0.28f, Math.Min(0.86f, baseA * 0.82f)) },
                    new SharpDX.Direct2D1.GradientStop { Position = 0.52f, Color = new Color4(0.08f, 0.86f, 0.62f, 0.94f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 1.00f, Color = new Color4(0.24f, 0.99f, 0.88f, 1.00f) }
                });
                dxStopsPut = new SharpDX.Direct2D1.GradientStopCollection(RenderTarget, new SharpDX.Direct2D1.GradientStop[] {
                    new SharpDX.Direct2D1.GradientStop { Position = 0.00f, Color = new Color4(0.32f, 0.04f, 0.12f, baseA * 0.52f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 0.58f, Color = new Color4(0.90f, 0.18f, 0.35f, Math.Min(0.92f, baseA * 1.18f)) },
                    new SharpDX.Direct2D1.GradientStop { Position = 1.00f, Color = new Color4(1.00f, 0.28f, 0.54f, Math.Min(0.98f, baseA * 1.38f)) }
                });
                dxStopsPutHeavy = new SharpDX.Direct2D1.GradientStopCollection(RenderTarget, new SharpDX.Direct2D1.GradientStop[] {
                    new SharpDX.Direct2D1.GradientStop { Position = 0.00f, Color = new Color4(0.42f, 0.05f, 0.16f, Math.Min(0.86f, baseA * 0.82f)) },
                    new SharpDX.Direct2D1.GradientStop { Position = 0.52f, Color = new Color4(0.96f, 0.20f, 0.40f, 0.94f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 1.00f, Color = new Color4(1.00f, 0.34f, 0.66f, 1.00f) }
                });

                var props = new SharpDX.Direct2D1.LinearGradientBrushProperties {
                    StartPoint = new SharpDX.Vector2(0f, 0f),
                    EndPoint = new SharpDX.Vector2(100f, 0f)
                };
                dxGradCall = new SharpDX.Direct2D1.LinearGradientBrush(RenderTarget, props, dxStopsCall);
                dxGradCallHeavy = new SharpDX.Direct2D1.LinearGradientBrush(RenderTarget, props, dxStopsCallHeavy);
                dxGradPut = new SharpDX.Direct2D1.LinearGradientBrush(RenderTarget, props, dxStopsPut);
                dxGradPutHeavy = new SharpDX.Direct2D1.LinearGradientBrush(RenderTarget, props, dxStopsPutHeavy);
                cachedOpacidade = safeOpacity;
                cachedCanvasRight = -1f;
            }
        }

        private bool TagColide(SharpDX.RectangleF candidate) {
            for (int i = 0; i < usedTagRects.Count; i++) {
                SharpDX.RectangleF b = usedTagRects[i];
                if (candidate.Left < b.Right && candidate.Right > b.Left && candidate.Top < b.Bottom && candidate.Bottom > b.Top)
                    return true;
            }
            return false;
        }

        protected override void OnRender(ChartControl chartControl, ChartScale chartScale) {
            if (niveisGamma.Count == 0 || chartControl == null || chartScale == null || RenderTarget == null) return;

            int safeOpacity = (Opacidade > 0 && Opacidade <= 100) ? Opacidade : 58;
            int safeLarguraMax = (LarguraMax > 20) ? LarguraMax : 300;
            float maxBarH = (EspessuraMax >= 4 && EspessuraMax <= 24) ? (float)EspessuraMax : 10f;

            string estilo = string.IsNullOrWhiteSpace(EfeitoVisual) ? "NEON_GLOW" : EfeitoVisual.Trim().ToUpperInvariant();
            bool isEco = (estilo == "ECO");
            bool useGlow = (estilo == "NEON_GLOW");
            bool useGradient = !isEco;

            EnsureStaticResources(safeOpacity);

            float panelLeft = (ChartPanel != null) ? (float)ChartPanel.X : 0f;
            float panelTop = (ChartPanel != null) ? (float)ChartPanel.Y : 0f;
            float panelRight = (ChartPanel != null) ? (float)(ChartPanel.X + ChartPanel.W) : (float)chartControl.ActualWidth;
            float panelBottom = (ChartPanel != null) ? (float)(ChartPanel.Y + ChartPanel.H) : (float)chartControl.ActualHeight;
            float canvasRight = Math.Max(panelLeft + 40f, panelRight - 3f);

            if (Math.Abs(cachedCanvasRight - canvasRight) > 0.5f || cachedLarguraMax != safeLarguraMax) {
                var sp = new SharpDX.Vector2(canvasRight, 0f);
                var ep = new SharpDX.Vector2(canvasRight - safeLarguraMax, 0f);
                dxGradCall.StartPoint = sp; dxGradCall.EndPoint = ep;
                dxGradCallHeavy.StartPoint = sp; dxGradCallHeavy.EndPoint = ep;
                dxGradPut.StartPoint = sp; dxGradPut.EndPoint = ep;
                dxGradPutHeavy.StartPoint = sp; dxGradPutHeavy.EndPoint = ep;
                cachedCanvasRight = canvasRight;
                cachedLarguraMax = safeLarguraMax;
            }

            string modo = (ModoHistograma ?? "GAMMA").Trim().ToUpperInvariant();
            double maxG = 0;
            for (int i = 0; i < niveisGamma.Count; i++) {
                double val = Math.Abs(ObterValorMetrica(niveisGamma[i], modo));
                if (val > maxG) maxG = val;
            }
            if (maxG <= 0) return;

            usedTagRects.Clear();

            for (int i = 0; i < niveisGamma.Count; i++) {
                var n = niveisGamma[i];
                float y = (float)chartScale.GetYByValue(n.Strike);
                if (y < panelTop - 20f || y > panelBottom + 20f) continue;

                double metricVal = ObterValorMetrica(n, modo);
                double ratio = Math.Abs(metricVal) / maxG;
                float w = (float)(ratio * safeLarguraMax);
                if (w < 3f) continue;

                bool isCall = metricVal > 0;
                bool hasLabel = !string.IsNullOrEmpty(n.Label);
                bool isHeavy = (ratio > 0.65 || hasLabel);

                float h = (ratio > 0.72) ? maxBarH : (ratio > 0.40 ? Math.Max(4.5f, maxBarH * 0.72f) : Math.Max(3.0f, maxBarH * 0.44f));
                float barLeft = canvasRight - w;
                float barTop = y - h * 0.5f;
                float rad = Math.Min(h * 0.48f, w * 0.48f);

                SharpDX.RectangleF barRect = new SharpDX.RectangleF(barLeft, barTop, w, h);
                SharpDX.Direct2D1.RoundedRectangle roundedBar = new SharpDX.Direct2D1.RoundedRectangle { Rect = barRect, RadiusX = rad, RadiusY = rad };

                // Camada 1: Glow Neon Geométrico Ultra-Leve (zero shader pesado de VRAM)
                if (useGlow && ratio > 0.34) {
                    if (isHeavy) {
                        SharpDX.Direct2D1.RoundedRectangle outerGlow = new SharpDX.Direct2D1.RoundedRectangle {
                            Rect = new SharpDX.RectangleF(barLeft - 4f, barTop - 4f, w + 4f, h + 8f),
                            RadiusX = rad + 3f, RadiusY = rad + 3f
                        };
                        RenderTarget.FillRoundedRectangle(outerGlow, isCall ? dxBrushCallGlowOuter : dxBrushPutGlowOuter);
                    }
                    SharpDX.Direct2D1.RoundedRectangle innerGlow = new SharpDX.Direct2D1.RoundedRectangle {
                        Rect = new SharpDX.RectangleF(barLeft - 2f, barTop - 2f, w + 2f, h + 4f),
                        RadiusX = rad + 1.5f, RadiusY = rad + 1.5f
                    };
                    RenderTarget.FillRoundedRectangle(innerGlow, isCall ? dxBrushCallGlow : dxBrushPutGlow);
                }

                // Camada 2: Corpo Principal em Degradê Linear Horizontal (pré-cacheado)
                SharpDX.Direct2D1.Brush fillBrush = useGradient
                    ? (SharpDX.Direct2D1.Brush)(isCall ? (isHeavy ? dxGradCallHeavy : dxGradCall) : (isHeavy ? dxGradPutHeavy : dxGradPut))
                    : (SharpDX.Direct2D1.Brush)(isCall ? dxBrushCall : dxBrushPut);

                if (!isEco) RenderTarget.FillRoundedRectangle(roundedBar, fillBrush);
                else RenderTarget.FillRectangle(barRect, fillBrush);

                // Contorno fino elegante apenas em barras principais / Walls
                if (isHeavy && !isEco) {
                    SharpDX.Direct2D1.Brush borderBrush = isCall ? dxBrushCallTip : dxBrushPutTip;
                    RenderTarget.DrawRoundedRectangle(roundedBar, borderBrush, hasLabel ? 0.95f : 0.55f);
                }

                // Camada 3: Reflexo Specular Glass 3D no topo da barra + Ponta Neon ("Leading Cap")
                if (!isEco && w >= 14f && h >= 5.0f) {
                    SharpDX.RectangleF specRect = new SharpDX.RectangleF(barLeft + rad * 0.6f, barTop + 0.9f, Math.Max(4f, w - rad * 1.2f), 1.25f);
                    RenderTarget.FillRectangle(specRect, dxBrushSpecular);
                }
                if (!isEco && w >= 7f && ratio > 0.25) {
                    float capW = isHeavy ? 3.2f : 2.2f;
                    SharpDX.Direct2D1.RoundedRectangle tipCap = new SharpDX.Direct2D1.RoundedRectangle {
                        Rect = new SharpDX.RectangleF(barLeft, barTop + 0.6f, capW, Math.Max(2f, h - 1.2f)),
                        RadiusX = 1.2f, RadiusY = 1.2f
                    };
                    SharpDX.Direct2D1.Brush capBrush = n.IsNewMoney
                        ? dxBrushNewMoney
                        : (isCall ? dxBrushCallTip : dxBrushPutTip);
                    RenderTarget.FillRoundedRectangle(tipCap, capBrush);
                }

                // Camada 4: Pílula de Texto Moderna com Anti-Colisão Vertical
                string txt = (modo == "GAMMA") ? FormatVal(metricVal) : FormatContracts(metricVal);
                if (n.IsNewMoney && !string.IsNullOrEmpty(txt)) txt = txt + " [OPEN$]";
                if (hasLabel) txt = n.Label + (string.IsNullOrEmpty(txt) ? "" : " " + txt);

                if ((hasLabel || ratio > 0.25) && !string.IsNullOrEmpty(txt)) {
                    float charW = hasLabel ? 7.0f : 6.4f;
                    float badgeH = hasLabel ? 18f : 16f;
                    float badgeW = Math.Max(48f, txt.Length * charW + 16f);
                    float boxLeft = Math.Max(panelLeft + 6f, barLeft - badgeW - 8f);

                    float chosenTop = Math.Max(panelTop + 4f, Math.Min(panelBottom - badgeH - 4f, y - badgeH * 0.5f));
                    if (TagColide(new SharpDX.RectangleF(boxLeft - 2f, chosenTop - 1f, badgeW + 4f, badgeH + 2f))) {
                        float[] dyOffsets = { -19f, 19f, -38f, 38f };
                        foreach (float dy in dyOffsets) {
                            float candTop = Math.Max(panelTop + 4f, Math.Min(panelBottom - badgeH - 4f, (y + dy) - badgeH * 0.5f));
                            if (!TagColide(new SharpDX.RectangleF(boxLeft - 2f, candTop - 1f, badgeW + 4f, badgeH + 2f))) {
                                chosenTop = candTop;
                                break;
                            }
                        }
                    }

                    SharpDX.RectangleF tagRect = new SharpDX.RectangleF(boxLeft, chosenTop, badgeW, badgeH);
                    usedTagRects.Add(new SharpDX.RectangleF(boxLeft - 2f, chosenTop - 1f, badgeW + 4f, badgeH + 2f));

                    float tagMidY = chosenTop + badgeH * 0.5f;
                    if (Math.Abs(tagMidY - y) > 4f && barLeft > tagRect.Right + 2f) {
                        RenderTarget.DrawLine(new SharpDX.Vector2(tagRect.Right, tagMidY), new SharpDX.Vector2(barLeft - 1f, y), dxBrushLeader, 0.9f);
                    }

                    SharpDX.Direct2D1.Brush accentBrush = hasLabel
                        ? (isCall ? dxBrushCallTip : dxBrushPutTip)
                        : (n.IsNewMoney ? dxBrushNewMoney : (isCall ? dxBrushCallTip : dxBrushPutTip));

                    SharpDX.Direct2D1.RoundedRectangle pill = new SharpDX.Direct2D1.RoundedRectangle { Rect = tagRect, RadiusX = 4f, RadiusY = 4f };
                    RenderTarget.FillRoundedRectangle(pill, dxBrushLabelBg);
                    RenderTarget.DrawRoundedRectangle(pill, hasLabel ? accentBrush : dxBrushLabelBorder, hasLabel ? 0.95f : 0.7f);

                    // Faixa indicadora lateral esquerda dentro da pílula
                    RenderTarget.FillRectangle(new SharpDX.RectangleF(boxLeft + 2f, chosenTop + 3f, 2.5f, badgeH - 6f), accentBrush);

                    SharpDX.Direct2D1.Brush txtColor = hasLabel ? dxBrushHighlight : (n.IsNewMoney ? dxBrushNewMoney : dxBrushText);
                    RenderTarget.DrawText(txt, hasLabel ? dxTextFormatBold : dxTextFormat, new SharpDX.RectangleF(boxLeft + 8f, chosenTop + 2f, badgeW - 10f, badgeH - 2f), txtColor);
                }
            }
        }

        private void DisporBrushesDinamicos() {
            if (dxBrushCall != null) { dxBrushCall.Dispose(); dxBrushCall = null; }
            if (dxBrushPut != null) { dxBrushPut.Dispose(); dxBrushPut = null; }
            if (dxGradCall != null) { dxGradCall.Dispose(); dxGradCall = null; }
            if (dxGradPut != null) { dxGradPut.Dispose(); dxGradPut = null; }
            if (dxGradCallHeavy != null) { dxGradCallHeavy.Dispose(); dxGradCallHeavy = null; }
            if (dxGradPutHeavy != null) { dxGradPutHeavy.Dispose(); dxGradPutHeavy = null; }
            if (dxStopsCall != null) { dxStopsCall.Dispose(); dxStopsCall = null; }
            if (dxStopsPut != null) { dxStopsPut.Dispose(); dxStopsPut = null; }
            if (dxStopsCallHeavy != null) { dxStopsCallHeavy.Dispose(); dxStopsCallHeavy = null; }
            if (dxStopsPutHeavy != null) { dxStopsPutHeavy.Dispose(); dxStopsPutHeavy = null; }
            cachedOpacidade = -1;
            cachedCanvasRight = -1f;
            cachedLarguraMax = -1;
        }

        private void LimparRecursos() {
            DisporBrushesDinamicos();
            if (dxBrushCallGlow != null) { dxBrushCallGlow.Dispose(); dxBrushCallGlow = null; }
            if (dxBrushPutGlow != null) { dxBrushPutGlow.Dispose(); dxBrushPutGlow = null; }
            if (dxBrushCallGlowOuter != null) { dxBrushCallGlowOuter.Dispose(); dxBrushCallGlowOuter = null; }
            if (dxBrushPutGlowOuter != null) { dxBrushPutGlowOuter.Dispose(); dxBrushPutGlowOuter = null; }
            if (dxBrushCallTip != null) { dxBrushCallTip.Dispose(); dxBrushCallTip = null; }
            if (dxBrushPutTip != null) { dxBrushPutTip.Dispose(); dxBrushPutTip = null; }
            if (dxBrushSpecular != null) { dxBrushSpecular.Dispose(); dxBrushSpecular = null; }
            if (dxBrushText != null) { dxBrushText.Dispose(); dxBrushText = null; }
            if (dxBrushHighlight != null) { dxBrushHighlight.Dispose(); dxBrushHighlight = null; }
            if (dxBrushNewMoney != null) { dxBrushNewMoney.Dispose(); dxBrushNewMoney = null; }
            if (dxBrushLabelBg != null) { dxBrushLabelBg.Dispose(); dxBrushLabelBg = null; }
            if (dxBrushLabelBorder != null) { dxBrushLabelBorder.Dispose(); dxBrushLabelBorder = null; }
            if (dxBrushLeader != null) { dxBrushLeader.Dispose(); dxBrushLeader = null; }
            if (dxTextFormat != null) { dxTextFormat.Dispose(); dxTextFormat = null; }
            if (dxTextFormatBold != null) { dxTextFormatBold.Dispose(); dxTextFormatBold = null; }
            if (dxFactory != null) { dxFactory.Dispose(); dxFactory = null; }
        }

        public override void OnRenderTargetChanged() {
            LimparRecursos();
        }

        private bool LerTudo() {
            try {
                if(Instrument==null)return false;
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
                string dte = (VencimentoDTE ?? "ALL").Trim().ToUpperInvariant();
                string suffix = (dte == "0DTE" || dte == "1DTE" || dte == "2DTE" || dte == "7DTE") ? ("_" + dte) : "";
                string f1 = Path.Combine(pastaGexData, "NiveisGamma_" + s + suffix + ".csv");
                string f2 = Path.Combine(pastaGexData, "GammaProfile_" + s + suffix + ".csv");
                if (!File.Exists(f2) && suffix == "_0DTE") {
                    f1 = Path.Combine(pastaGexData, "NiveisGamma_" + s + "_1DTE.csv");
                    f2 = Path.Combine(pastaGexData, "GammaProfile_" + s + "_1DTE.csv");
                }
                if (!File.Exists(f2)) {
                    f1 = Path.Combine(pastaGexData, "NiveisGamma_" + s + ".csv");
                    f2 = Path.Combine(pastaGexData, "GammaProfile_" + s + ".csv");
                }
                long t1 = File.Exists(f1) ? File.GetLastWriteTimeUtc(f1).Ticks : 0L;
                long t2 = File.Exists(f2) ? File.GetLastWriteTimeUtc(f2).Ticks : 0L;
                string sig = f1 + "|" + t1 + "|" + f2 + "|" + t2;
                if (sig == ultimaAssinaturaCsv && niveisGamma.Count > 0) return false;
                if(File.Exists(f1)) {
                    string txt1 = LerTextoCompartilhado(f1);
                    if (!string.IsNullOrWhiteSpace(txt1)) {
                        var p = txt1.Split(',');
                        if(p.Length>=5) { AddL(map, p[0], "CW"); AddL(map, p[1], "PW"); AddL(map, p[2], "ZG"); }
                    }
                }
                if(File.Exists(f2)) {
                    using(var fs = new FileStream(f2, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                    using(var sr = new StreamReader(fs)) {
                        sr.ReadLine();
                        while(!sr.EndOfStream) {
                            string rawLine = sr.ReadLine();
                            if (string.IsNullOrWhiteSpace(rawLine)) continue;
                            var ln = rawLine.Split(',');
                            if(ln.Length>=2) {
                                double st, ng, coi=0, poi=0, cvol=0, pvol=0;
                                if(double.TryParse(ln[0], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out st) &&
                                   double.TryParse(ln[1], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out ng)) {
                                    if(ln.Length>=6) {
                                        double.TryParse(ln[2], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out cvol);
                                        double.TryParse(ln[3], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out pvol);
                                        double.TryParse(ln[4], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out coi);
                                        double.TryParse(ln[5], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out poi);
                                    }
                                    string lb = map.ContainsKey(st) ? map[st] : "";
                                    bool isNew = (cvol > coi && cvol > 100) || (Math.Abs(pvol) > Math.Abs(poi) && Math.Abs(pvol) > 100);
                                    novos.Add(new GammaLevel{
                                        Strike=st, NetGamma=ng,
                                        CallOI=coi, PutOI=Math.Abs(poi),
                                        CallVol=cvol, PutVol=Math.Abs(pvol),
                                        Label=lb, IsNewMoney=isNew
                                    });
                                }
                            }
                        }
                    }
                }
                if(novos.Count>0) {
                    niveisGamma=novos;
                    ultimaAssinaturaCsv = sig;
                    return true;
                }
            } catch{}
            return false;
        }
        private string LerTextoCompartilhado(string path) {
            using (FileStream fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
            using (StreamReader sr = new StreamReader(fs))
                return sr.ReadToEnd();
        }
        private void AddL(System.Collections.Generic.Dictionary<double,string> d, string v, string t) {
            if(double.TryParse(v, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out double val)) d[val]=t;
        }
        private string FormatVal(double v) {
            double a = Math.Abs(v); string s = v<0?"-":"";
            if(a>=1e9) return s+"$"+(a/1e9).ToString("F1")+"B";
            if(a>=1e6) return s+"$"+(a/1e6).ToString("F1")+"M";
            if(a>=1e3) return s+"$"+Math.Round(a/1e3).ToString("F0")+"k";
            return "";
        }
        private string FormatContracts(double v) {
            double a = Math.Abs(v); string s = v<0?"-":"+";
            if(a>=1e3) return s+(a/1e3).ToString("F1")+"k ctrs";
            if(a>=1) return s+Math.Round(a).ToString("F0")+" ctrs";
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
using System.Collections.Generic;
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
        private class LabelItem
        {
            public string Key;
            public string Text;
            public double Price;
            public SharpDX.Color4 Color;
            public bool Bold;
            public int Priority;
        }

        private DateTime ultimaLeitura = DateTime.MinValue;
        private string pastaGexData = @"C:\Users\alanb\Dropbox\Dropbox\Aplicativos\RoboGexNinjaV1"; 
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

        private SimpleFont fonteDash;
        private bool legacyCleared = false;

        private SharpDX.DirectWrite.Factory dxFactory;
        private SharpDX.DirectWrite.TextFormat dxFmtRegular, dxFmtBold;
        private SharpDX.Direct2D1.SolidColorBrush dxBgBrush, dxLeaderBrush, dxBorderNeutralBrush;
        private SharpDX.Direct2D1.StrokeStyle dxStrokeDash, dxStrokeDot;
        private readonly Dictionary<string, SharpDX.Direct2D1.SolidColorBrush> dxColorBrushes = new Dictionary<string, SharpDX.Direct2D1.SolidColorBrush>();

        [NinjaScriptProperty] [XmlIgnore] [Display(Name="Cor Call Wall", Order=1, GroupName="Cores")] public System.Windows.Media.Brush CorCallWall { get; set; }
        [NinjaScriptProperty] [XmlIgnore] [Display(Name="Cor Put Wall", Order=2, GroupName="Cores")] public System.Windows.Media.Brush CorPutWall { get; set; }
        [NinjaScriptProperty] [Display(Name="Margem Direita Tags (px)", Order=3, GroupName="Cores")] public int MargemDireitaTags { get; set; }
        [Browsable(false)] public string CorCallWallSerialize { get { return Serialize.BrushToString(CorCallWall); } set { CorCallWall = Serialize.StringToBrush(value); } }
        [Browsable(false)] public string CorPutWallSerialize { get { return Serialize.BrushToString(CorPutWall); } set { CorPutWall = Serialize.StringToBrush(value); } }

        protected override void OnStateChange() {
            if (State == State.SetDefaults) {
                Name = "VeltrixQuant - NiveisGammaPro"; Calculate = Calculate.OnEachTick; IsOverlay = true; DisplayInDataBox = true; DrawOnPricePanel = true; ScaleJustification = NinjaTrader.Gui.Chart.ScaleJustification.Right;
                CorCallWall = System.Windows.Media.Brushes.Cyan; CorPutWall = System.Windows.Media.Brushes.Magenta; MargemDireitaTags = 370;
            } else if (State == State.Terminated) {
                LimparRecursos();
            }
        }

        protected override void OnBarUpdate() {
            if (DateTime.Now > ultimaLeitura.AddSeconds(3)) {
                LerArquivos();
                CriarPinceis();
                Desenhar();
                ultimaLeitura = DateTime.Now;
                ForceRefresh();
            }
        }

        private void CriarPinceis() {
            if (fonteDash == null) fonteDash = new SimpleFont("Consolas", 10) { Bold = true };
        }

        private void Desenhar() {
            if (!legacyCleared) {
                string[] oldTags = {
                    "CW", "TxtCW", "PW", "TxtPW", "DP", "TxtDP", "ZG", "TxtZG", "MP", "TxtMP",
                    "CW0DTE", "TxtCW0DTE", "PW0DTE", "TxtPW0DTE", "ZG0DTE", "TxtZG0DTE",
                    "CW1DTE", "TxtCW1DTE", "PW1DTE", "TxtPW1DTE", "ZG1DTE", "TxtZG1DTE",
                    "CW2DTE", "TxtCW2DTE", "PW2DTE", "TxtPW2DTE", "ZG2DTE", "TxtZG2DTE",
                    "CW7DTE", "TxtCW7DTE", "PW7DTE", "TxtPW7DTE", "ZG7DTE", "TxtZG7DTE"
                };
                foreach (string t in oldTags) RemoveDrawObject(t);
                legacyCleared = true;
            }

            System.Windows.Media.Brush corFundoDash = System.Windows.Media.Brushes.Black;
            System.Windows.Media.Brush corTextoRegime = System.Windows.Media.Brushes.White;
            
            if (dashRegime.Contains("SHORT")) { corFundoDash = System.Windows.Media.Brushes.DarkRed; corTextoRegime = System.Windows.Media.Brushes.Yellow; }
            else if (dashRegime.Contains("LONG")) { corFundoDash = System.Windows.Media.Brushes.DarkGreen; corTextoRegime = System.Windows.Media.Brushes.White; }

            string titulo = "🛡️ QUANT ENGINE V8\n------------------";
            string fonte = string.IsNullOrEmpty(dashSource) ? "" : "\nFONTE: " + dashSource;
            string flipStatus = !niveisDisponiveis
                ? "GEX: arquivo de niveis indisponivel"
                : zeroGamma > 0
                    ? "GEX FLIP (Zero Gamma): " + zeroGamma
                    : "GEX FLIP: sem cruzamento na faixa";
            double ratioNum = 0;
            double.TryParse(dashRatio, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out ratioNum);
            string ratioTag = ratioNum > 1.20 ? "[PUT DOMINANT]" : (ratioNum > 0 && ratioNum < 0.80 ? "[CALL DOMINANT]" : "[NEUTRAL]");
            string niveisResumo = "\nPOS GEX (CW): " + callWall + " (" + cwMoney + ") | NEG GEX (PW): " + putWall + " (" + pwMoney + ")"
                + "\nMAX PAIN: " + maxPain + " | BLOCK/MAX VOL: " + optionVolumeStrike + " (" + optionVolume + " ctrs)";
            string alvosResumo = (dashAlvoUp != "0" && dashAlvoDown != "0") ? "\nALVOS VOL: " + dashAlvoDown + " <-> " + dashAlvoUp : "";
            string ivLabel = string.IsNullOrWhiteSpace(dashIvSource) ? "IV BASE" : dashIvSource.ToUpperInvariant();
            string dados = "\nREGIME: " + dashRegime + "\n------------------" + "\nCALL/PUT VOLUME BALANCE (source/model units): " + dashNetFlow + " (" + dashFlowVal + ")" + "\nNET GEX: " + dashNetGex + " (" + dashGexVal + ")" + niveisResumo + "\n" + flipStatus + "\nRATIO: " + dashRatio + " " + ratioTag + "\n" + ivLabel + ": " + dashIv + "%" + alvosResumo + fonte + "\nATUALIZADO: " + DateTime.Now.ToString("HH:mm:ss");
            Draw.TextFixed(this, "DashFundo", titulo + dados, TextPosition.TopLeft, corTextoRegime, fonteDash, corFundoDash, System.Windows.Media.Brushes.Black, 100);
        }

        private SharpDX.Color4 ToColor4(System.Windows.Media.Brush brush, SharpDX.Color4 fallback) {
            var sb = brush as System.Windows.Media.SolidColorBrush;
            if (sb == null) return fallback;
            var c = sb.Color;
            return new SharpDX.Color4(c.R / 255f, c.G / 255f, c.B / 255f, 1.0f);
        }

        private SharpDX.Direct2D1.SolidColorBrush GetDxBrush(string key, SharpDX.Color4 col) {
            SharpDX.Direct2D1.SolidColorBrush b;
            if (!dxColorBrushes.TryGetValue(key, out b) || b == null) {
                b = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, col);
                dxColorBrushes[key] = b;
            }
            return b;
        }

        protected override void OnRender(ChartControl chartControl, ChartScale chartScale) {
            if (chartControl == null || chartScale == null || ChartPanel == null || RenderTarget == null) return;

            if (dxFactory == null) dxFactory = new SharpDX.DirectWrite.Factory();
            if (dxFmtRegular == null) dxFmtRegular = new SharpDX.DirectWrite.TextFormat(dxFactory, "Consolas", SharpDX.DirectWrite.FontWeight.SemiBold, SharpDX.DirectWrite.FontStyle.Normal, 10f);
            if (dxFmtBold == null) dxFmtBold = new SharpDX.DirectWrite.TextFormat(dxFactory, "Consolas", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 10.5f);
            if (dxBgBrush == null) dxBgBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.03f, 0.05f, 0.09f, 0.96f));
            if (dxBorderNeutralBrush == null) dxBorderNeutralBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.28f, 0.36f, 0.50f, 0.72f));
            if (dxLeaderBrush == null) dxLeaderBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.75f, 0.84f, 0.96f, 0.70f));
            if (dxStrokeDash == null) {
                dxStrokeDash = new SharpDX.Direct2D1.StrokeStyle(
                    NinjaTrader.Core.Globals.D2DFactory,
                    new SharpDX.Direct2D1.StrokeStyleProperties { DashStyle = SharpDX.Direct2D1.DashStyle.Dash }
                );
            }
            if (dxStrokeDot == null) {
                dxStrokeDot = new SharpDX.Direct2D1.StrokeStyle(
                    NinjaTrader.Core.Globals.D2DFactory,
                    new SharpDX.Direct2D1.StrokeStyleProperties { DashStyle = SharpDX.Direct2D1.DashStyle.Dot }
                );
            }

            var items = new List<LabelItem>();
            SharpDX.Color4 cwCol = ToColor4(CorCallWall, new SharpDX.Color4(0f, 1f, 1f, 1f));
            SharpDX.Color4 pwCol = ToColor4(CorPutWall, new SharpDX.Color4(1f, 0f, 1f, 1f));

            if (optionVolumeStrike > 0) items.Add(new LabelItem { Key="DP", Text="MAX OPTION VOLUME | " + optionVolume + " ctrs [" + optionVolumeStrike + "]", Price=optionVolumeStrike, Color=new SharpDX.Color4(0.70f, 0.44f, 1f, 1f), Bold=true, Priority=1 });
            if (callWall > 0) items.Add(new LabelItem { Key="CW", Text="CALL WALL | " + cwMoney + " [" + callWall + "]", Price=callWall, Color=cwCol, Bold=true, Priority=2 });
            if (putWall > 0) items.Add(new LabelItem { Key="PW", Text="PUT WALL | " + pwMoney + " [" + putWall + "]", Price=putWall, Color=pwCol, Bold=true, Priority=3 });
            if (zeroGamma > 0) items.Add(new LabelItem { Key="ZG", Text="GEX FLIP [" + zeroGamma + "]", Price=zeroGamma, Color=new SharpDX.Color4(1f, 1f, 1f, 1f), Bold=true, Priority=4 });
            if (maxPain > 0) items.Add(new LabelItem { Key="MP", Text="MAX PAIN [" + maxPain + "]", Price=maxPain, Color=new SharpDX.Color4(0.95f, 0.76f, 0.20f, 1f), Bold=true, Priority=5 });

            if (cw0DTE > 0) items.Add(new LabelItem { Key="CW0DTE", Text="0DTE CALL WALL [" + cw0DTE + "]", Price=cw0DTE, Color=new SharpDX.Color4(1f, 0.95f, 0.25f, 1f), Bold=false, Priority=6 });
            if (pw0DTE > 0) items.Add(new LabelItem { Key="PW0DTE", Text="0DTE PUT WALL [" + pw0DTE + "]", Price=pw0DTE, Color=new SharpDX.Color4(1f, 0.55f, 0.10f, 1f), Bold=false, Priority=7 });
            if (zg0DTE > 0) items.Add(new LabelItem { Key="ZG0DTE", Text="0DTE GEX FLIP [" + zg0DTE + "]", Price=zg0DTE, Color=new SharpDX.Color4(1f, 0.84f, 0.20f, 1f), Bold=false, Priority=8 });
            if (cw1DTE > 0) items.Add(new LabelItem { Key="CW1DTE", Text="1DTE CALL WALL [" + cw1DTE + "]", Price=cw1DTE, Color=new SharpDX.Color4(0.25f, 0.65f, 1f, 1f), Bold=false, Priority=9 });
            if (pw1DTE > 0) items.Add(new LabelItem { Key="PW1DTE", Text="1DTE PUT WALL [" + pw1DTE + "]", Price=pw1DTE, Color=new SharpDX.Color4(0.65f, 0.48f, 0.92f, 1f), Bold=false, Priority=10 });
            if (zg1DTE > 0) items.Add(new LabelItem { Key="ZG1DTE", Text="1DTE GEX FLIP [" + zg1DTE + "]", Price=zg1DTE, Color=new SharpDX.Color4(0.53f, 0.81f, 0.98f, 1f), Bold=false, Priority=11 });
            if (cw2DTE > 0) items.Add(new LabelItem { Key="CW2DTE", Text="2DTE CALL WALL [" + cw2DTE + "]", Price=cw2DTE, Color=new SharpDX.Color4(0.20f, 0.95f, 0.95f, 1f), Bold=false, Priority=12 });
            if (pw2DTE > 0) items.Add(new LabelItem { Key="PW2DTE", Text="2DTE PUT WALL [" + pw2DTE + "]", Price=pw2DTE, Color=new SharpDX.Color4(0.95f, 0.35f, 0.90f, 1f), Bold=false, Priority=13 });
            if (zg2DTE > 0) items.Add(new LabelItem { Key="ZG2DTE", Text="2DTE GEX FLIP [" + zg2DTE + "]", Price=zg2DTE, Color=new SharpDX.Color4(0.85f, 0.68f, 0.25f, 1f), Bold=false, Priority=14 });
            if (cw7DTE > 0) items.Add(new LabelItem { Key="CW7DTE", Text="7DTE CALL WALL [" + cw7DTE + "]", Price=cw7DTE, Color=new SharpDX.Color4(0.30f, 0.85f, 0.35f, 1f), Bold=false, Priority=15 });
            if (pw7DTE > 0) items.Add(new LabelItem { Key="PW7DTE", Text="7DTE PUT WALL [" + pw7DTE + "]", Price=pw7DTE, Color=new SharpDX.Color4(1f, 0.42f, 0.32f, 1f), Bold=false, Priority=16 });
            if (zg7DTE > 0) items.Add(new LabelItem { Key="ZG7DTE", Text="7DTE GEX FLIP [" + zg7DTE + "]", Price=zg7DTE, Color=new SharpDX.Color4(0.78f, 0.82f, 0.86f, 1f), Bold=false, Priority=17 });

            if (items.Count == 0) return;

            float panelLeft = (float)ChartPanel.X;
            float panelTop = (float)ChartPanel.Y;
            float panelRight = (float)(ChartPanel.X + ChartPanel.W);
            float panelBottom = (float)(ChartPanel.Y + ChartPanel.H);
            float rightMargin = (MargemDireitaTags > 0 && MargemDireitaTags != 190) ? MargemDireitaTags : 370f;

            // Passo 1: Feixes horizontais estilizados em SharpDX (desenhados ANTES das tags para ZERO corte no texto!)
            foreach (var item in items) {
                float lineY = (float)chartScale.GetYByValue(item.Price);
                if (lineY < panelTop + 2f || lineY > panelBottom - 2f) continue;

                bool isMainWall = (item.Key == "CW" || item.Key == "PW" || item.Key == "DP");
                bool isZg = item.Key.StartsWith("ZG");
                bool isMp = (item.Key == "MP");

                SharpDX.Vector2 pStart = new SharpDX.Vector2(panelLeft, lineY);
                SharpDX.Vector2 pEnd = new SharpDX.Vector2(panelRight, lineY);

                if (isMainWall) {
                    var glowBrush = GetDxBrush("GLOW_" + item.Key, new SharpDX.Color4(item.Color.Red, item.Color.Green, item.Color.Blue, 0.16f));
                    var coreBrush = GetDxBrush("CORE_" + item.Key, new SharpDX.Color4(item.Color.Red, item.Color.Green, item.Color.Blue, 0.88f));
                    RenderTarget.DrawLine(pStart, pEnd, glowBrush, 5.0f);
                    RenderTarget.DrawLine(pStart, pEnd, coreBrush, 1.5f);
                } else if (isZg || isMp) {
                    var glowBrush = GetDxBrush("GLOW_" + item.Key, new SharpDX.Color4(item.Color.Red, item.Color.Green, item.Color.Blue, 0.10f));
                    var coreBrush = GetDxBrush("CORE_" + item.Key, new SharpDX.Color4(item.Color.Red, item.Color.Green, item.Color.Blue, 0.82f));
                    RenderTarget.DrawLine(pStart, pEnd, glowBrush, 3.6f);
                    RenderTarget.DrawLine(pStart, pEnd, coreBrush, 1.3f, isZg ? dxStrokeDot : dxStrokeDash);
                } else {
                    var dteBrush = GetDxBrush("LINE_" + item.Key, new SharpDX.Color4(item.Color.Red, item.Color.Green, item.Color.Blue, 0.66f));
                    RenderTarget.DrawLine(pStart, pEnd, dteBrush, item.Key.Contains("0DTE") ? 1.35f : 1.05f, isZg ? dxStrokeDot : dxStrokeDash);
                }
            }

            // Passo 2: Etiquetas flutuantes ACIMA da linha (nunca no meio do traço) com pílula arredondada & anti-colisão
            SharpDX.RectangleF hudReserve = new SharpDX.RectangleF(panelLeft, panelTop, 420f, 235f);
            var placedRects = new List<SharpDX.RectangleF>();

            items.Sort((a, b) => a.Priority.CompareTo(b.Priority));

            foreach (var item in items) {
                float rawY = (float)chartScale.GetYByValue(item.Price);
                if (rawY < panelTop + 8f || rawY > panelBottom - 8f) continue;

                float charW = item.Bold ? 6.8f : 6.4f;
                float boxW = Math.Max(110f, item.Text.Length * charW + 18f);
                float boxH = item.Bold ? 18f : 17f;

                SharpDX.RectangleF chosen = new SharpDX.RectangleF();
                bool found = false;

                // Prioriza ficar ACIMA (-15px) ou ABAIXO (+15px) da linha para nunca ser cortada ao meio!
                float[] dyCandidates = { -15f, 15f, -36f, 36f, -57f, 57f, -78f, 78f, -99f, 99f, -120f, 120f, -141f, 141f, -162f, 162f, -183f, 183f };
                float[] dxLanes = { 0f, -280f, -560f };

                foreach (float dy in dyCandidates) {
                    float centerY = Math.Max(panelTop + boxH * 0.5f + 4f, Math.Min(panelBottom - boxH * 0.5f - 4f, rawY + dy));
                    float topY = centerY - boxH * 0.5f;

                    foreach (float dx in dxLanes) {
                        float boxRight = Math.Min(panelRight - 8f, panelRight - rightMargin + dx);
                        float boxLeft = boxRight - boxW;
                        if (boxLeft < panelLeft + 8f) {
                            if (dx < 0f) continue;
                            boxLeft = panelLeft + 8f;
                            boxRight = Math.Min(panelRight - 6f, boxLeft + boxW);
                        }
                        if (boxRight > panelRight - 6f) continue;

                        SharpDX.RectangleF candidate = new SharpDX.RectangleF(boxLeft, topY, boxW, boxH);
                        SharpDX.RectangleF padded = new SharpDX.RectangleF(boxLeft - 4f, topY - 2f, boxW + 8f, boxH + 4f);

                        if (RectOverlaps(padded, hudReserve) && (panelRight - panelLeft) > (boxW + 450f)) continue;

                        bool collides = false;
                        foreach (var pr in placedRects) {
                            if (RectOverlaps(padded, pr)) { collides = true; break; }
                        }
                        if (!collides) {
                            chosen = candidate;
                            found = true;
                            break;
                        }
                    }
                    if (found) break;
                }

                if (!found) {
                    float fallbackY = Math.Max(panelTop + 6f, Math.Min(panelBottom - boxH - 6f, rawY - boxH - 4f));
                    float fallbackX = Math.Max(panelLeft + 8f, panelRight - rightMargin - boxW);
                    chosen = new SharpDX.RectangleF(fallbackX, fallbackY, boxW, boxH);
                }

                placedRects.Add(chosen);

                var accentBrush = GetDxBrush(item.Key, item.Color);

                // Pequena haste vertical ligando a etiqueta à linha horizontal + ponto indicador na linha
                float pinX = Math.Min(panelRight - 8f, chosen.Right - 10f);
                float pinStartY = (chosen.Top + chosen.Height * 0.5f < rawY) ? chosen.Bottom : chosen.Top;
                if (Math.Abs(pinStartY - rawY) >= 2f && Math.Abs(pinStartY - rawY) <= 165f) {
                    RenderTarget.DrawLine(new SharpDX.Vector2(pinX, pinStartY), new SharpDX.Vector2(pinX, rawY), dxLeaderBrush, 0.9f);
                    RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(new SharpDX.Vector2(pinX, rawY), 2.3f, 2.3f), accentBrush);
                }

                SharpDX.Direct2D1.RoundedRectangle pill = new SharpDX.Direct2D1.RoundedRectangle { Rect = chosen, RadiusX = 4f, RadiusY = 4f };
                RenderTarget.FillRoundedRectangle(pill, dxBgBrush);
                RenderTarget.DrawRoundedRectangle(pill, item.Bold ? (SharpDX.Direct2D1.Brush)accentBrush : (SharpDX.Direct2D1.Brush)dxBorderNeutralBrush, item.Bold ? 1.0f : 0.75f);
                RenderTarget.FillRectangle(new SharpDX.RectangleF(chosen.Left + 2.5f, chosen.Top + 3f, 2.5f, chosen.Height - 6f), accentBrush);

                SharpDX.RectangleF textRect = new SharpDX.RectangleF(chosen.Left + 8f, chosen.Top + 2f, chosen.Width - 11f, chosen.Height - 2f);
                RenderTarget.DrawText(item.Text, item.Bold ? dxFmtBold : dxFmtRegular, textRect, accentBrush);
            }
        }

        private bool RectOverlaps(SharpDX.RectangleF a, SharpDX.RectangleF b) {
            return a.Left < b.Right && a.Right > b.Left && a.Top < b.Bottom && a.Bottom > b.Top;
        }

        private void LimparRecursos() {
            foreach (var kv in dxColorBrushes) { if (kv.Value != null) kv.Value.Dispose(); }
            dxColorBrushes.Clear();
            if (dxBgBrush != null) { dxBgBrush.Dispose(); dxBgBrush = null; }
            if (dxBorderNeutralBrush != null) { dxBorderNeutralBrush.Dispose(); dxBorderNeutralBrush = null; }
            if (dxLeaderBrush != null) { dxLeaderBrush.Dispose(); dxLeaderBrush = null; }
            if (dxStrokeDash != null) { dxStrokeDash.Dispose(); dxStrokeDash = null; }
            if (dxStrokeDot != null) { dxStrokeDot.Dispose(); dxStrokeDot = null; }
            if (dxFmtRegular != null) { dxFmtRegular.Dispose(); dxFmtRegular = null; }
            if (dxFmtBold != null) { dxFmtBold.Dispose(); dxFmtBold = null; }
            if (dxFactory != null) { dxFactory.Dispose(); dxFactory = null; }
        }

        public override void OnRenderTargetChanged() {
            LimparRecursos();
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
                    string txt1 = LerTextoCompartilhado(f1);
                    if (!string.IsNullOrWhiteSpace(txt1)) {
                    var p = txt1.Split(',');
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
                }
                double cw0File = 0, pw0File = 0;
                LerNiveisDte(s, "0DTE", out cw0File, out pw0File, out zg0DTE);
                if (cw0DTE == 0) cw0DTE = cw0File;
                if (pw0DTE == 0) pw0DTE = pw0File;
                LerNiveisDte(s, "1DTE", out cw1DTE, out pw1DTE, out zg1DTE);
                LerNiveisDte(s, "2DTE", out cw2DTE, out pw2DTE, out zg2DTE);
                LerNiveisDte(s, "7DTE", out cw7DTE, out pw7DTE, out zg7DTE);
                string f2 = Path.Combine(pastaGexData, "AlvosVolatilidade_" + s + ".csv");
                if (File.Exists(f2)) { 
                    string txt2 = LerTextoCompartilhado(f2);
                    if (!string.IsNullOrWhiteSpace(txt2)) {
                    var p = txt2.Split(','); 
                    if (p.Length >= 9) { 
                        double.TryParse(p[0], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out maxPain); 
                        double.TryParse(p[1], System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out optionVolumeStrike); 
                        double ivTemp = 0;
                        string rawIv = p[3].Replace("%", "").Trim();
                        string formattedIv = double.TryParse(rawIv, System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out ivTemp)
                            ? ivTemp.ToString("F1", System.Globalization.CultureInfo.InvariantCulture)
                            : rawIv;
                        var ptBr = new System.Globalization.CultureInfo("pt-BR");
                        double volTemp = 0, flowTemp = 0;
                        string formattedOptVol = double.TryParse(p[6].Trim(), System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out volTemp)
                            ? Math.Round(volTemp).ToString("N0", ptBr)
                            : p[6].Trim();
                        string formattedFlowVal = double.TryParse(p[7].Trim(), System.Globalization.NumberStyles.Any, System.Globalization.CultureInfo.InvariantCulture, out flowTemp)
                            ? Math.Round(flowTemp).ToString("N0", ptBr)
                            : p[7].Trim();
                        dashRatio = p[2]; dashIv = formattedIv; dashNetFlow = p[4]; dashNetGex = p[5]; optionVolume = formattedOptVol; dashFlowVal = formattedFlowVal; dashGexVal = p[8]; 
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
                }
            } catch (Exception ex) { niveisDisponiveis=false; Print("NiveisGammaPro: falha ao ler CSV GEX: " + ex.Message); }
        }

        private string LerTextoCompartilhado(string path) {
            using (FileStream fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
            using (StreamReader sr = new StreamReader(fs))
                return sr.ReadToEnd();
        }

        private void LerNiveisDte(string symbol, string dte, out double call, out double put, out double zero) {
            call=0; put=0; zero=0;
            string path = Path.Combine(pastaGexData, "NiveisGamma_" + symbol + "_" + dte + ".csv");
            if (!File.Exists(path)) return;
            string txt = LerTextoCompartilhado(path);
            if (string.IsNullOrWhiteSpace(txt)) return;
            string[] values = txt.Split(',');
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

        [NinjaScriptProperty] [Display(Name="Vencimento DTE (ALL, 0DTE, 1DTE, 2DTE, 7DTE)", Order=8, GroupName="2. Estratégia")] 
        public string VencimentoDTE { get; set; }

        private SimpleFont ft1, ft2;
        private double currentIV = 0;
        private string currentIVSource = "IV base assumida";
        private string currentRegime = "Neutro";
        private double dailyExpectedMove = 0;
        private string pastaGexData = @"C:\Users\alanb\Dropbox\Dropbox\Aplicativos\RoboGexNinjaV1";
        private DateTime ultimaLeitura = DateTime.MinValue;
        private ATR indicadorATR; 

        protected override void OnStateChange() {
            if(State==State.SetDefaults){ 
                Name="VeltrixQuant - MoneyRiskPro"; 
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
                VencimentoDTE = "ALL";
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
            try {
                if(Instrument==null) {
                    currentIV = 0;
                    currentRegime = "Neutro";
                    return;
                }
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

                string dte = (VencimentoDTE ?? "ALL").Trim().ToUpperInvariant();
                string suffix = (dte == "0DTE" || dte == "1DTE" || dte == "2DTE" || dte == "7DTE") ? ("_" + dte) : "";
                string f = Path.Combine(pastaGexData, "AlvosVolatilidade_" + s + suffix + ".csv");
                if (!File.Exists(f) && suffix == "_0DTE") f = Path.Combine(pastaGexData, "AlvosVolatilidade_" + s + "_1DTE.csv");
                if (!File.Exists(f)) f = Path.Combine(pastaGexData, "AlvosVolatilidade_" + s + ".csv");
                if(!File.Exists(f)) {
                    currentIV = 0;
                    currentRegime = "Neutro";
                    return;
                }
                string content = "";
                using (FileStream fs = new FileStream(f, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (StreamReader sr = new StreamReader(fs))
                    content = sr.ReadToEnd();
                if (string.IsNullOrWhiteSpace(content)) return;
                currentIV = 0;
                currentRegime = "Neutro";
                var lines = content.Split(','); 
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
                Name = "VeltrixQuant - DailyOHLCPro";
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
                Name = "VeltrixQuant - GlobexRangePro";
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

            int t = ToTime(Time[0]) / 100;
            int tPrev = ToTime(Time[1]) / 100;
            
            if (t >= HoraInicio && tPrev < HoraInicio) 
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
            
            if (inSession && t >= HoraFim && tPrev < HoraFim)
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
        private string pastaIvData = @"C:\Users\alanb\Dropbox\Dropbox\Aplicativos\RoboGexNinjaV1"; 
        
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
        [Display(Name="Vencimento DTE (ALL, 0DTE, 1DTE, 2DTE, 7DTE)", Order=2, GroupName="1. Parâmetros Base")]
        public string VencimentoDTE { get; set; }

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
                Name = "VeltrixQuant - VolatilidadeImplicitaPro"; 
                Description = "Plota faixas estimadas de 1, 2 e 3 desvios da IV-base, ancoradas na abertura da sessão.";
                Calculate = Calculate.OnEachTick; 
                IsOverlay = true;
                IvManual = 0;
                VencimentoDTE = "ALL";

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

                string dte = (VencimentoDTE ?? "ALL").Trim().ToUpperInvariant();
                string suffix = (dte == "0DTE" || dte == "1DTE" || dte == "2DTE" || dte == "7DTE") ? ("_" + dte) : "";
                string file = Path.Combine(pastaIvData, "AlvosVolatilidade_" + s + suffix + ".csv");
                if (!File.Exists(file) && suffix == "_0DTE") file = Path.Combine(pastaIvData, "AlvosVolatilidade_" + s + "_1DTE.csv");
                if (!File.Exists(file)) file = Path.Combine(pastaIvData, "AlvosVolatilidade_" + s + ".csv");
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
        private DateTime ultimaLeituraDropbox = DateTime.MinValue;
        private string pastaGexData = @"C:\Users\alanb\Dropbox\Dropbox\Aplicativos\RoboGexNinjaV1";
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
        [Display(Name = "3. Vencimento DTE (ALL, 0DTE, 1DTE, 2DTE, 7DTE)", GroupName = "1. Automação do VIX", Order = 3)]
        public string VencimentoDTE { get; set; }

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
                Name = "VeltrixQuant - FluentliExpectedMove";
                Calculate = Calculate.OnBarClose;
                IsOverlay = true;
                DisplayInDataBox = false;

                UsarVixAutomatico = true; 
                VixManual = 15.0; 
                VencimentoDTE = "ALL";
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
                    if (!carregouCsv && IsSp500Instrument())
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
                string dte = (VencimentoDTE ?? "ALL").Trim().ToUpperInvariant();
                string suffix = (dte == "0DTE" || dte == "1DTE" || dte == "2DTE" || dte == "7DTE") ? ("_" + dte) : "";
                string file = Path.Combine(pastaGexData, "AlvosVolatilidade_" + sym + suffix + ".csv");
                if (!File.Exists(file) && suffix == "_0DTE") file = Path.Combine(pastaGexData, "AlvosVolatilidade_" + sym + "_1DTE.csv");
                if (!File.Exists(file)) file = Path.Combine(pastaGexData, "AlvosVolatilidade_" + sym + ".csv");
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

            if (UsarVixAutomatico && DateTime.Now > ultimaLeituraDropbox.AddSeconds(5))
            {
                TentarCarregarIvDoDropbox();
                ultimaLeituraDropbox = DateTime.Now;
            }

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
# 8. VWAP INSTITUCIONAL PRO (COM NINJASCRIPT GENERATED WRAPPER)
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
        private double closedSumVol = 0;
        private double closedVwap = 0;
        private double closedM2 = 0;
        private int lastCommittedBar = -1;
        private int sessionStartBar = -1;

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
                Description = "VWAP Institucional Welford com 4 Bandas Proporcionais ao Desvio Maximo";
                Name = "VeltrixQuant - VWAPInstitucionalPro";
                Calculate = Calculate.OnEachTick;
                IsOverlay = true;
                DrawOnPricePanel = true;
                ScaleJustification = NinjaTrader.Gui.Chart.ScaleJustification.Right;

                NumBandas = 4;
                MostrarBandas = true;
                ResetDiario = true;
                DesvioMaximo = 2.0;

                AddPlot(new Stroke(Brushes.Yellow, DashStyleHelper.Solid, 2), PlotStyle.Line, "VWAP");
                AddPlot(new Stroke(Brushes.DodgerBlue, DashStyleHelper.Dot, 1), PlotStyle.Line, "Top SD1");
                AddPlot(new Stroke(Brushes.DodgerBlue, DashStyleHelper.Dot, 1), PlotStyle.Line, "Bot SD1");
                AddPlot(new Stroke(Brushes.Cyan, DashStyleHelper.Dash, 1), PlotStyle.Line, "Top SD2");
                AddPlot(new Stroke(Brushes.Cyan, DashStyleHelper.Dash, 1), PlotStyle.Line, "Bot SD2");
                AddPlot(new Stroke(Brushes.Orange, DashStyleHelper.Dash, 2), PlotStyle.Line, "Top SD3");
                AddPlot(new Stroke(Brushes.Orange, DashStyleHelper.Dash, 2), PlotStyle.Line, "Bot SD3");
                AddPlot(new Stroke(Brushes.Red, DashStyleHelper.Solid, 2), PlotStyle.Line, "Top SD4");
                AddPlot(new Stroke(Brushes.Red, DashStyleHelper.Solid, 2), PlotStyle.Line, "Bot SD4");
            }
            else if (State == State.DataLoaded)
            {
                closedSumVol = 0;
                closedVwap = 0;
                closedM2 = 0;
                lastCommittedBar = -1;
                sessionStartBar = -1;
            }
        }

        private void AcumularWelford(double tp, double vol, ref double sVol, ref double mean, ref double m2)
        {
            if (vol <= 0) return;
            double nextVol = sVol + vol;
            double delta = tp - mean;
            double nextMean = mean + (vol / nextVol) * delta;
            m2 += vol * delta * (tp - nextMean);
            mean = nextMean;
            sVol = nextVol;
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < 0) return;

            if (CurrentBar > lastCommittedBar)
            {
                if (lastCommittedBar >= 0)
                {
                    if (ResetDiario && Bars.IsFirstBarOfSession)
                    {
                        closedSumVol = 0;
                        closedVwap = 0;
                        closedM2 = 0;
                        sessionStartBar = CurrentBar;
                    }
                    else
                    {
                        double prevTp = (High[1] + Low[1] + Close[1]) / 3.0;
                        double prevVol = Math.Max(0, Volume[1]);
                        AcumularWelford(prevTp, prevVol, ref closedSumVol, ref closedVwap, ref closedM2);
                    }
                }
                else
                {
                    sessionStartBar = CurrentBar;
                }
                lastCommittedBar = CurrentBar;
            }

            if (sessionStartBar < 0) sessionStartBar = CurrentBar;

            double curVol = Math.Max(0, Volume[0]);
            double curTp = (High[0] + Low[0] + Close[0]) / 3.0;

            double totVol = closedSumVol;
            double vwapValue = closedVwap;
            double m2 = closedM2;

            AcumularWelford(curTp, curVol, ref totVol, ref vwapValue, ref m2);

            if (totVol <= 0)
            {
                Values[0][0] = curTp;
                return;
            }

            double variance = Math.Max(0.0, m2 / totVol);
            double stdDevValue = Math.Sqrt(variance);

            Values[0][0] = vwapValue;

            if (MostrarBandas)
            {
                int safeBandas = Math.Max(1, Math.Min(4, NumBandas));
                double safeDesvio = (DesvioMaximo > 0.0 && DesvioMaximo <= 6.0) ? DesvioMaximo : 2.0;
                double step = safeDesvio / safeBandas;

                if (safeBandas >= 1)
                {
                    double d1 = step * 1.0 * stdDevValue;
                    Values[1][0] = vwapValue + d1;
                    Values[2][0] = vwapValue - d1;
                }
                if (safeBandas >= 2)
                {
                    double d2 = step * 2.0 * stdDevValue;
                    Values[3][0] = vwapValue + d2;
                    Values[4][0] = vwapValue - d2;
                }
                if (safeBandas >= 3)
                {
                    double d3 = step * 3.0 * stdDevValue;
                    Values[5][0] = vwapValue + d3;
                    Values[6][0] = vwapValue - d3;
                }
                if (safeBandas >= 4)
                {
                    double d4 = step * 4.0 * stdDevValue;
                    Values[7][0] = vwapValue + d4;
                    Values[8][0] = vwapValue - d4;
                }
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
            return VWAPInstitucionalPro(Input, 4, true, true, 2.0);
        }

        public VWAPInstitucionalPro VWAPInstitucionalPro(ISeries<double> input)
        {
            return VWAPInstitucionalPro(input, 4, true, true, 2.0);
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
            return indicator.VWAPInstitucionalPro(Input, 4, true, true, 2.0);
        }

        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro(ISeries<double> input)
        {
            return indicator.VWAPInstitucionalPro(input, 4, true, true, 2.0);
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
            return indicator.VWAPInstitucionalPro(Input, 4, true, true, 2.0);
        }

        public Indicators.VWAPInstitucionalPro VWAPInstitucionalPro(ISeries<double> input)
        {
            return indicator.VWAPInstitucionalPro(input, 4, true, true, 2.0);
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

# ==============================================================================
# 9. DELTA CUMULATIVE PRO v2.0 (COM NINJASCRIPT GENERATED WRAPPER)
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
                Name = "VeltrixQuant - DeltaCumulativePro";
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

# ==============================================================================
# ARQUIVO 10: FluentliWatchdog (Icebergs Dinâmicos & Sintéticos - SharpDX)
# ==============================================================================
CODE_WATCHDOG = r"""
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
"""

# ==============================================================================
# 11. DARK POOL BEAMS PRO (FEIXES LILAS + FINRA BARRA DE FORCA + CORRELACAO)
# ==============================================================================
CODE_DARKPOOL_BEAMS = r'''using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Windows.Media;
using System.Windows.Threading;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.NinjaScript;
using SharpDX;
using SharpDX.Direct2D1;
using SharpDX.DirectWrite;

namespace NinjaTrader.NinjaScript.Indicators
{
    public class DarkPoolBeamsPro : Indicator
    {
        private class DpBeam
        {
            public string Etf;
            public string FutureTarget;
            public string TimeEt;
            public string TimeBrt;
            public string DateLabel;
            public bool IsToday;
            public double EtfPrice;
            public double ProjectedFuture;
            public double BarVolume;
            public double NotionalM;
            public double RvolBar;
            public double AbsorptionScore;
            public string SideBias;
            public string Classification;
        }

        private class FinraSummary
        {
            public bool HasData;
            public string Symbol;
            public string FutureTarget;
            public string Date;
            public double TotalVol;
            public double ShortVol;
            public double NonShortVol;
            public double ShortPct;
            public double NonShortPct;
            public double Price;
            public double NotionalM;
            public string FlowTag;
            public string Signal;
        }

        private sealed class VeltrixTimeoutWebClient : WebClient
        {
            private readonly int timeoutMs;
            public VeltrixTimeoutWebClient(int timeoutMs)
            {
                this.timeoutMs = timeoutMs;
            }

            protected override WebRequest GetWebRequest(Uri address)
            {
                ServicePointManager.SecurityProtocol |= (SecurityProtocolType)3072 | (SecurityProtocolType)768 | SecurityProtocolType.Tls;
                WebRequest req = base.GetWebRequest(address);
                if (req != null) req.Timeout = timeoutMs;
                HttpWebRequest http = req as HttpWebRequest;
                if (http != null)
                {
                    http.UserAgent = "VeltrixQuant-NT8/1.0";
                    http.AutomaticDecompression = DecompressionMethods.GZip | DecompressionMethods.Deflate;
                }
                return req;
            }
        }

        private sealed class VeltrixJsonParser
        {
            private readonly string json;
            private int idx;

            private VeltrixJsonParser(string src)
            {
                json = src ?? "";
                idx = 0;
            }

            public static object Parse(string src)
            {
                if (string.IsNullOrEmpty(src)) return null;
                VeltrixJsonParser p = new VeltrixJsonParser(src);
                return p.ParseValue();
            }

            private void SkipWs()
            {
                while (idx < json.Length && char.IsWhiteSpace(json[idx])) idx++;
            }

            private object ParseValue()
            {
                SkipWs();
                if (idx >= json.Length) return null;
                char c = json[idx];
                if (c == '{') return ParseObject();
                if (c == '[') return ParseArray();
                if (c == '"') return ParseString();
                if (c == 't') { idx += 4; return true; }
                if (c == 'f') { idx += 5; return false; }
                if (c == 'n') { idx += 4; return null; }
                return ParseNumber();
            }

            private Dictionary<string, object> ParseObject()
            {
                Dictionary<string, object> map = new Dictionary<string, object>(StringComparer.OrdinalIgnoreCase);
                idx++;
                while (idx < json.Length)
                {
                    SkipWs();
                    if (idx >= json.Length) break;
                    if (json[idx] == '}') { idx++; break; }
                    if (json[idx] == ',') { idx++; continue; }
                    string key = ParseString();
                    SkipWs();
                    if (idx < json.Length && json[idx] == ':') idx++;
                    object val = ParseValue();
                    if (key != null) map[key] = val;
                }
                return map;
            }

            private List<object> ParseArray()
            {
                List<object> list = new List<object>();
                idx++;
                while (idx < json.Length)
                {
                    SkipWs();
                    if (idx >= json.Length) break;
                    if (json[idx] == ']') { idx++; break; }
                    if (json[idx] == ',') { idx++; continue; }
                    list.Add(ParseValue());
                }
                return list;
            }

            private string ParseString()
            {
                if (idx >= json.Length || json[idx] != '"') return string.Empty;
                idx++;
                StringBuilder sb = new StringBuilder();
                while (idx < json.Length)
                {
                    char c = json[idx++];
                    if (c == '"') break;
                    if (c == '\\' && idx < json.Length)
                    {
                        char esc = json[idx++];
                        switch (esc)
                        {
                            case '"': sb.Append('"'); break;
                            case '\\': sb.Append('\\'); break;
                            case '/': sb.Append('/'); break;
                            case 'b': sb.Append('\b'); break;
                            case 'f': sb.Append('\f'); break;
                            case 'n': sb.Append('\n'); break;
                            case 'r': sb.Append('\r'); break;
                            case 't': sb.Append('\t'); break;
                            case 'u':
                                if (idx + 4 <= json.Length)
                                {
                                    int hex;
                                    if (int.TryParse(json.Substring(idx, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out hex))
                                        sb.Append((char)hex);
                                    idx += 4;
                                }
                                break;
                            default: sb.Append(esc); break;
                        }
                    }
                    else
                    {
                        sb.Append(c);
                    }
                }
                return sb.ToString();
            }

            private object ParseNumber()
            {
                int start = idx;
                while (idx < json.Length)
                {
                    char c = json[idx];
                    if ((c >= '0' && c <= '9') || c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E')
                        idx++;
                    else
                        break;
                }
                string token = json.Substring(start, Math.Max(0, idx - start));
                double num;
                if (double.TryParse(token, NumberStyles.Any, CultureInfo.InvariantCulture, out num))
                    return num;
                return 0.0;
            }

            public static Dictionary<string, object> AsDict(object obj) { return obj as Dictionary<string, object>; }
            public static List<object> AsList(object obj) { return obj as List<object>; }

            public static string Str(Dictionary<string, object> d, string key, string defVal)
            {
                if (d == null) return defVal;
                object v;
                if (!d.TryGetValue(key, out v) || v == null) return defVal;
                return Convert.ToString(v, CultureInfo.InvariantCulture) ?? defVal;
            }

            public static double Num(Dictionary<string, object> d, string key, double defVal)
            {
                if (d == null) return defVal;
                object v;
                if (!d.TryGetValue(key, out v) || v == null) return defVal;
                if (v is double) return (double)v;
                if (v is int) return (int)v;
                double parsed;
                if (double.TryParse(Convert.ToString(v, CultureInfo.InvariantCulture), NumberStyles.Any, CultureInfo.InvariantCulture, out parsed))
                    return parsed;
                return defVal;
            }

            public static bool Bool(Dictionary<string, object> d, string key, bool defVal)
            {
                if (d == null) return defVal;
                object v;
                if (!d.TryGetValue(key, out v) || v == null) return defVal;
                if (v is bool) return (bool)v;
                return defVal;
            }
        }

        private readonly object dataLock = new object();
        private List<DpBeam> activeBeams = new List<DpBeam>();
        private FinraSummary finraSummary = new FinraSummary();
        private double latestEtfRefPrice = 0;
        private string feedStatusMsg = "AGUARDANDO CONEXAO...";
        private string resolvedUrlInUse = "http://localhost:3000";
        private bool apiOnline = false;
        private DateTime lastSyncLocal = DateTime.MinValue;

        private string chartRoot = "ES";
        private string targetEtf = "SPY";
        private string targetDisplay = "S&P 500";
        private bool isEtfDirectChart = false;

        private Timer pollTimer;
        private int isFetchingFlag = 0;
        private DispatcherTimer pulseTimer;

        // SharpDX GPU resources
        private SharpDX.Direct2D1.LinearGradientBrush dxGradLilac;
        private SharpDX.Direct2D1.LinearGradientBrush dxGradBid;
        private SharpDX.Direct2D1.LinearGradientBrush dxGradAsk;
        private SharpDX.Direct2D1.GradientStopCollection dxStopsLilac;
        private SharpDX.Direct2D1.GradientStopCollection dxStopsBid;
        private SharpDX.Direct2D1.GradientStopCollection dxStopsAsk;

        private SharpDX.Direct2D1.SolidColorBrush dxAuraLilac;
        private SharpDX.Direct2D1.SolidColorBrush dxAuraBid;
        private SharpDX.Direct2D1.SolidColorBrush dxAuraAsk;
        private SharpDX.Direct2D1.SolidColorBrush dxCoreLilac;
        private SharpDX.Direct2D1.SolidColorBrush dxCoreBid;
        private SharpDX.Direct2D1.SolidColorBrush dxCoreAsk;
        private SharpDX.Direct2D1.SolidColorBrush dxPillBg;
        private SharpDX.Direct2D1.SolidColorBrush dxPillBorder;
        private SharpDX.Direct2D1.SolidColorBrush dxTextBright;
        private SharpDX.Direct2D1.SolidColorBrush dxTextMuted;
        private SharpDX.Direct2D1.SolidColorBrush dxBarTrack;
        private SharpDX.Direct2D1.SolidColorBrush dxFinraCardBg;
        private SharpDX.Direct2D1.SolidColorBrush dxLeader;
        private SharpDX.DirectWrite.Factory dxDwFactory;
        private SharpDX.DirectWrite.TextFormat dxFontMain;
        private SharpDX.DirectWrite.TextFormat dxFontSmall;
        private SharpDX.DirectWrite.TextFormat dxFontTitle;

        private readonly List<SharpDX.RectangleF> usedTagsScratch = new List<SharpDX.RectangleF>();

        #region Propriedades
        [NinjaScriptProperty]
        [Display(Name = "URL Dashboard (AUTO ou URL)", Description = "AUTO le VeltrixQuant_URL.txt ou Vercel Cloud (gex-dashboard)", Order = 1, GroupName = "01. Conexao API")]
        public string DashboardUrl { get; set; }

        [NinjaScriptProperty]
        [Range(5, 300)]
        [Display(Name = "Atualizar a cada (Segundos)", Order = 2, GroupName = "01. Conexao API")]
        public int AtualizarSegundos { get; set; }

        [NinjaScriptProperty]
        [Range(1, 20)]
        [Display(Name = "Max Feixes Dark Pool no Grafico", Order = 3, GroupName = "02. Feixes e Pulso")]
        public int MaxFeixesVisiveis { get; set; }

        [NinjaScriptProperty]
        [Range(6, 200)]
        [Display(Name = "Largura do Feixe (Barras)", Order = 4, GroupName = "02. Feixes e Pulso")]
        public int LarguraFeixeBarras { get; set; }

        [NinjaScriptProperty]
        [Range(0.0, 5000.0)]
        [Display(Name = "Notional Minimo ($M, 0=Todos)", Order = 5, GroupName = "02. Feixes e Pulso")]
        public double NotionalMinMilhoes { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Ativar Feixe Piscante (Pulso)", Order = 6, GroupName = "02. Feixes e Pulso")]
        public bool AtivarFeixePiscante { get; set; }

        [NinjaScriptProperty]
        [Range(4, 600)]
        [Display(Name = "Distancia Pulso Forte (Ticks)", Order = 7, GroupName = "02. Feixes e Pulso")]
        public int DistanciaPulsoTicks { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Mostrar Card FINRA + Barra de Forca", Order = 8, GroupName = "03. Visual e HUD")]
        public bool MostrarBarraFinra { get; set; }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "Cor Base dos Feixes (Lilas)", Order = 9, GroupName = "03. Visual e HUD")]
        public System.Windows.Media.Brush CorFeixePrincipal { get; set; }

        [Browsable(false)]
        public string CorFeixePrincipalSerialize
        {
            get { return Serialize.BrushToString(CorFeixePrincipal); }
            set { CorFeixePrincipal = Serialize.StringToBrush(value); }
        }
        #endregion

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Feixes de Luz Lilas Dark Pool 1m (SEC/FINRA) correlacionados automaticamente a Futuros, Bonds, Metais e Acoes.";
                Name = "VeltrixQuant - DarkPoolBeamsPro";
                Calculate = Calculate.OnEachTick;
                IsOverlay = true;
                IsAutoScale = false;
                DisplayInDataBox = false;
                DrawOnPricePanel = true;
                PaintPriceMarkers = false;
                IsSuspendedWhileInactive = true;

                DashboardUrl = "AUTO";
                AtualizarSegundos = 20;
                MaxFeixesVisiveis = 8;
                LarguraFeixeBarras = 42;
                NotionalMinMilhoes = 0.0;
                AtivarFeixePiscante = true;
                DistanciaPulsoTicks = 48;
                MostrarBarraFinra = true;
                CorFeixePrincipal = Brushes.MediumOrchid;
            }
            else if (State == State.DataLoaded)
            {
                ResolveTargetBasket();
                resolvedUrlInUse = ResolveDashboardBaseUrl();
                StartPolling();
                StartPulseTimer();
            }
            else if (State == State.Terminated)
            {
                StopTimers();
                LimparRecursosRender();
            }
        }

        protected override void OnBarUpdate()
        {
        }

        private void ResolveTargetBasket()
        {
            string raw = (Instrument != null && Instrument.MasterInstrument != null && !string.IsNullOrEmpty(Instrument.MasterInstrument.Name))
                ? Instrument.MasterInstrument.Name.Trim().ToUpperInvariant()
                : "ES";
            string[] parts = raw.Split(new char[] { ' ', '-', '.', '/' }, StringSplitOptions.RemoveEmptyEntries);
            chartRoot = (parts.Length > 0) ? parts[0] : raw;

            isEtfDirectChart = false;
            if (chartRoot == "ES" || chartRoot == "MES" || chartRoot == "SPX" || chartRoot == "SPY")
            {
                targetEtf = "SPY"; targetDisplay = "S&P 500"; isEtfDirectChart = (chartRoot == "SPY");
            }
            else if (chartRoot == "NQ" || chartRoot == "MNQ" || chartRoot == "NDX" || chartRoot == "QQQ")
            {
                targetEtf = "QQQ"; targetDisplay = "Nasdaq 100"; isEtfDirectChart = (chartRoot == "QQQ");
            }
            else if (chartRoot == "RTY" || chartRoot == "M2K" || chartRoot == "RUT" || chartRoot == "IWM")
            {
                targetEtf = "IWM"; targetDisplay = "Russell 2000"; isEtfDirectChart = (chartRoot == "IWM");
            }
            else if (chartRoot == "YM" || chartRoot == "MYM" || chartRoot == "DJI" || chartRoot == "DIA")
            {
                targetEtf = "DIA"; targetDisplay = "Dow Jones"; isEtfDirectChart = (chartRoot == "DIA");
            }
            else if (chartRoot == "GC" || chartRoot == "MGC" || chartRoot == "XAU" || chartRoot == "GLD")
            {
                targetEtf = "GLD"; targetDisplay = "Ouro (GC)"; isEtfDirectChart = (chartRoot == "GLD");
            }
            else if (chartRoot == "ZB" || chartRoot == "UB" || chartRoot == "TLT")
            {
                targetEtf = "TLT"; targetDisplay = "Bonds 20Y (ZB)"; isEtfDirectChart = (chartRoot == "TLT");
            }
            else if (chartRoot == "ZN" || chartRoot == "ZF" || chartRoot == "ZT" || chartRoot == "IEF")
            {
                targetEtf = "IEF"; targetDisplay = "Notes 7-10Y (ZN)"; isEtfDirectChart = (chartRoot == "IEF");
            }
            else if (chartRoot == "CL" || chartRoot == "MCL" || chartRoot == "USO")
            {
                targetEtf = "USO"; targetDisplay = "WTI Crude (CL)"; isEtfDirectChart = (chartRoot == "USO");
            }
            else
            {
                targetEtf = chartRoot; targetDisplay = chartRoot; isEtfDirectChart = true;
            }
        }

        private string ResolveDashboardBaseUrl()
        {
            string manual = (DashboardUrl ?? string.Empty).Trim();
            if (!string.IsNullOrEmpty(manual) && !string.Equals(manual, "AUTO", StringComparison.OrdinalIgnoreCase))
                return manual.TrimEnd('/');

            try
            {
                string envUrl = Environment.GetEnvironmentVariable("VELTRIX_DASHBOARD_URL");
                if (!string.IsNullOrEmpty(envUrl)) return envUrl.Trim().TrimEnd('/');

                string docs = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                string[] cfgPaths = new string[]
                {
                    Path.Combine(docs, "NinjaTrader 8", "bin", "Custom", "Indicators", "VeltrixQuant", "VeltrixQuant_URL.txt"),
                    Path.Combine(docs, "NinjaTrader 8", "VeltrixQuant_URL.txt"),
                    Path.Combine(docs, "VeltrixQuant_URL.txt")
                };
                for (int i = 0; i < cfgPaths.Length; i++)
                {
                    if (File.Exists(cfgPaths[i]))
                    {
                        string fileUrl = File.ReadAllText(cfgPaths[i]).Trim();
                        if (!string.IsNullOrEmpty(fileUrl) && fileUrl.StartsWith("http", StringComparison.OrdinalIgnoreCase))
                            return fileUrl.TrimEnd('/');
                    }
                }
            }
            catch { }
            return "https://gex-dashboard-git-master-gex-cloud.vercel.app";
        }

        private string ResolveVercelBypassToken()
        {
            try
            {
                string envTok = Environment.GetEnvironmentVariable("VELTRIX_BYPASS_TOKEN");
                if (!string.IsNullOrEmpty(envTok)) return envTok.Trim();

                string docs = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                string[] tokPaths = new string[]
                {
                    Path.Combine(docs, "NinjaTrader 8", "bin", "Custom", "Indicators", "VeltrixQuant", "VeltrixQuant_BYPASS.txt"),
                    Path.Combine(docs, "NinjaTrader 8", "VeltrixQuant_BYPASS.txt"),
                    Path.Combine(docs, "VeltrixQuant_BYPASS.txt")
                };
                for (int i = 0; i < tokPaths.Length; i++)
                {
                    if (File.Exists(tokPaths[i]))
                    {
                        string tok = File.ReadAllText(tokPaths[i]).Trim();
                        if (!string.IsNullOrEmpty(tok)) return tok;
                    }
                }
            }
            catch { }
            return string.Empty;
        }
        {
            int intervalMs = Math.Max(5000, AtualizarSegundos * 1000);
            pollTimer = new Timer(_ => FetchDarkPoolAsync(), null, 350, intervalMs);
        }

        private void StartPulseTimer()
        {
            if (!AtivarFeixePiscante || ChartControl == null) return;
            ChartControl.Dispatcher.InvokeAsync(new Action(() =>
            {
                if (State == State.Terminated || ChartControl == null) return;
                pulseTimer = new DispatcherTimer(DispatcherPriority.Render, ChartControl.Dispatcher);
                pulseTimer.Interval = TimeSpan.FromMilliseconds(220);
                pulseTimer.Tick += (s, ev) =>
                {
                    if (ChartControl == null || State != State.Realtime) return;
                    bool hasBeams;
                    lock (dataLock) { hasBeams = activeBeams.Count > 0; }
                    if (hasBeams) ChartControl.InvalidateVisual();
                };
                pulseTimer.Start();
            }));
        }

        private void StopTimers()
        {
            try
            {
                if (pollTimer != null) { pollTimer.Dispose(); pollTimer = null; }
            }
            catch { }

            if (pulseTimer != null && ChartControl != null)
            {
                try
                {
                    ChartControl.Dispatcher.InvokeAsync(new Action(() =>
                    {
                        if (pulseTimer != null)
                        {
                            pulseTimer.Stop();
                            pulseTimer = null;
                        }
                    }));
                }
                catch { }
            }
        }

        private void FetchDarkPoolAsync()
        {
            if (State == State.Terminated) return;
            if (Interlocked.CompareExchange(ref isFetchingFlag, 1, 0) != 0) return;

            try
            {
                string primaryUrl = ResolveDashboardBaseUrl();
                string baseUrl = primaryUrl;
                string endpoint = baseUrl + "/api/macro-darkpool?only=darkpool";
                string payload = null;
                bool htmlBlocked = false;
                Exception lastEx = null;

                List<string> candList = new List<string>();
                candList.Add(primaryUrl);
                if (!candList.Exists(u => string.Equals(u, "http://localhost:3000", StringComparison.OrdinalIgnoreCase)))
                    candList.Add("http://localhost:3000");
                if (!candList.Exists(u => string.Equals(u, "http://127.0.0.1:3000", StringComparison.OrdinalIgnoreCase)))
                    candList.Add("http://127.0.0.1:3000");

                try { ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12; } catch { }

                string bypassToken = ResolveVercelBypassToken();
                Dictionary<string, object> root = null;
                Dictionary<string, object> dpObj = null;

                for (int c = 0; c < candList.Count; c++)
                {
                    baseUrl = candList[c];
                    endpoint = baseUrl + "/api/macro-darkpool?only=darkpool";
                    try
                    {
                        using (VeltrixTimeoutWebClient wc = new VeltrixTimeoutWebClient(20000))
                        {
                            wc.Encoding = Encoding.UTF8;
                            if (!string.IsNullOrEmpty(bypassToken) && baseUrl.IndexOf("vercel.app", StringComparison.OrdinalIgnoreCase) >= 0)
                                wc.Headers["x-vercel-protection-bypass"] = bypassToken;
                            payload = wc.DownloadString(endpoint);
                        }

                        if (!string.IsNullOrEmpty(payload) && payload.TrimStart().StartsWith("<", StringComparison.Ordinal))
                        {
                            htmlBlocked = true;
                            continue;
                        }

                        root = VeltrixJsonParser.AsDict(VeltrixJsonParser.Parse(payload));
                        dpObj = (root != null) ? VeltrixJsonParser.AsDict(root.ContainsKey("darkPool") ? root["darkPool"] : null) : null;
                        if (dpObj != null)
                        {
                            lastEx = null;
                            break;
                        }
                    }
                    catch (Exception ex)
                    {
                        lastEx = ex;
                    }
                }

                if (dpObj == null)
                {
                    lock (dataLock)
                    {
                        apiOnline = false;
                        resolvedUrlInUse = primaryUrl;
                        if (htmlBlocked)
                            feedStatusMsg = "VERCEL EXIGE LOGIN (Desligue Vercel Auth ou ligue localhost:3000)";
                        else if (lastEx != null)
                        {
                            string em = lastEx.Message ?? "Erro HTTP";
                            if (em.Length > 34) em = em.Substring(0, 34);
                            feedStatusMsg = "OFFLINE (" + em + ")";
                        }
                        else
                            feedStatusMsg = "RESPOSTA SEM DARKPOOL";
                    }
                    if (ChartControl != null)
                    {
                        ChartControl.Dispatcher.InvokeAsync(new Action(() =>
                        {
                            if (ChartControl != null && State != State.Terminated)
                                ChartControl.InvalidateVisual();
                        }));
                    }
                    return;
                }

                List<object> rawBlocks = VeltrixJsonParser.AsList(dpObj.ContainsKey("proxyBlocks") ? dpObj["proxyBlocks"] : null);
                Dictionary<string, object> finraObj = VeltrixJsonParser.AsDict(dpObj.ContainsKey("finra") ? dpObj["finra"] : null);
                List<object> finraRows = (finraObj != null) ? VeltrixJsonParser.AsList(finraObj.ContainsKey("rows") ? finraObj["rows"] : null) : null;
                string finraDate = VeltrixJsonParser.Str(finraObj, "date", string.Empty);

                List<DpBeam> matchedBeams = new List<DpBeam>();
                List<DpBeam> fallbackTltForZn = new List<DpBeam>();
                double foundEtfPrice = 0;

                if (rawBlocks != null)
                {
                    for (int i = 0; i < rawBlocks.Count; i++)
                    {
                        Dictionary<string, object> b = VeltrixJsonParser.AsDict(rawBlocks[i]);
                        if (b == null) continue;
                        string etf = VeltrixJsonParser.Str(b, "etf", string.Empty).ToUpperInvariant();
                        string fut = VeltrixJsonParser.Str(b, "futureTarget", string.Empty).ToUpperInvariant();
                        double notional = VeltrixJsonParser.Num(b, "notionalUsdMillions", 0.0);
                        if (notional < NotionalMinMilhoes) continue;

                        DpBeam item = new DpBeam
                        {
                            Etf = etf,
                            FutureTarget = fut,
                            TimeEt = VeltrixJsonParser.Str(b, "timeEt", string.Empty),
                            TimeBrt = VeltrixJsonParser.Str(b, "timeBrt", string.Empty),
                            DateLabel = VeltrixJsonParser.Str(b, "dateLabel", string.Empty),
                            IsToday = VeltrixJsonParser.Bool(b, "isTodaySession", false),
                            EtfPrice = VeltrixJsonParser.Num(b, "etfPrice", 0.0),
                            ProjectedFuture = VeltrixJsonParser.Num(b, "projectedFutureLevel", 0.0),
                            BarVolume = VeltrixJsonParser.Num(b, "barVolume", 0.0),
                            NotionalM = notional,
                            RvolBar = VeltrixJsonParser.Num(b, "rvolBar", 1.0),
                            AbsorptionScore = VeltrixJsonParser.Num(b, "absorptionScore", 50.0),
                            SideBias = VeltrixJsonParser.Str(b, "sideBias", "NEUTRAL CLUSTER").ToUpperInvariant(),
                            Classification = VeltrixJsonParser.Str(b, "classification", string.Empty)
                        };

                        bool exactEtfMatch = (etf == targetEtf);
                        bool targetContainsRoot = (!string.IsNullOrEmpty(fut) && (fut == chartRoot || fut.Contains(chartRoot + " ") || fut.Contains("(" + chartRoot + ")")));

                        if (exactEtfMatch || targetContainsRoot)
                        {
                            matchedBeams.Add(item);
                            if (foundEtfPrice <= 0 && item.EtfPrice > 0) foundEtfPrice = item.EtfPrice;
                        }
                        else if (targetEtf == "IEF" && etf == "TLT")
                        {
                            fallbackTltForZn.Add(item);
                        }
                    }
                }

                if (matchedBeams.Count == 0 && targetEtf == "IEF" && fallbackTltForZn.Count > 0)
                    matchedBeams.AddRange(fallbackTltForZn);

                matchedBeams.Sort((a, b) =>
                {
                    int c = b.AbsorptionScore.CompareTo(a.AbsorptionScore);
                    return (c != 0) ? c : b.NotionalM.CompareTo(a.NotionalM);
                });
                if (matchedBeams.Count > MaxFeixesVisiveis)
                    matchedBeams.RemoveRange(MaxFeixesVisiveis, matchedBeams.Count - MaxFeixesVisiveis);

                FinraSummary summary = new FinraSummary { HasData = false, Date = finraDate };
                if (finraRows != null)
                {
                    for (int i = 0; i < finraRows.Count; i++)
                    {
                        Dictionary<string, object> r = VeltrixJsonParser.AsDict(finraRows[i]);
                        if (r == null) continue;
                        string sym = VeltrixJsonParser.Str(r, "symbol", string.Empty).ToUpperInvariant();
                        string fut = VeltrixJsonParser.Str(r, "futureTarget", string.Empty).ToUpperInvariant();
                        if (sym == targetEtf || fut == chartRoot || (targetEtf == "IEF" && sym == "TLT" && !summary.HasData))
                        {
                            summary.HasData = true;
                            summary.Symbol = sym;
                            summary.FutureTarget = fut;
                            summary.Date = VeltrixJsonParser.Str(r, "date", finraDate);
                            summary.TotalVol = VeltrixJsonParser.Num(r, "totalVolume", 0.0);
                            summary.ShortVol = VeltrixJsonParser.Num(r, "shortVolume", 0.0);
                            summary.NonShortVol = VeltrixJsonParser.Num(r, "nonShortVolume", 0.0);
                            summary.ShortPct = VeltrixJsonParser.Num(r, "shortPct", 50.0);
                            summary.NonShortPct = VeltrixJsonParser.Num(r, "nonShortPct", 50.0);
                            summary.Price = VeltrixJsonParser.Num(r, "price", 0.0);
                            summary.NotionalM = VeltrixJsonParser.Num(r, "notionalUsdMillions", 0.0);
                            summary.FlowTag = VeltrixJsonParser.Str(r, "flowTag", "NEUTRAL").ToUpperInvariant();
                            summary.Signal = VeltrixJsonParser.Str(r, "signal", string.Empty);
                            if (foundEtfPrice <= 0 && summary.Price > 0) foundEtfPrice = summary.Price;
                            if (sym == targetEtf) break;
                        }
                    }
                }

                lock (dataLock)
                {
                    activeBeams = matchedBeams;
                    finraSummary = summary;
                    latestEtfRefPrice = foundEtfPrice;
                    resolvedUrlInUse = baseUrl;
                    apiOnline = true;
                    lastSyncLocal = DateTime.Now;
                    feedStatusMsg = (matchedBeams.Count > 0)
                        ? ("ON · " + matchedBeams.Count + " FEIXES")
                        : ("ON · SEM BLOCO (" + targetEtf + ")");
                }

                if (ChartControl != null)
                {
                    ChartControl.Dispatcher.InvokeAsync(new Action(() =>
                    {
                        if (ChartControl != null && State != State.Terminated)
                            ChartControl.InvalidateVisual();
                    }));
                }
            }
            catch (Exception ex)
            {
                lock (dataLock)
                {
                    apiOnline = false;
                    string msg = ex.Message ?? "Erro HTTP";
                    if (msg.Length > 34) msg = msg.Substring(0, 34);
                    feedStatusMsg = "OFFLINE (" + msg + ")";
                }
            }
            finally
            {
                Interlocked.Exchange(ref isFetchingFlag, 0);
            }
        }

        private double ResolveChartLevel(DpBeam beam, double currentClose)
        {
            if (isEtfDirectChart && beam.EtfPrice > 0)
                return beam.EtfPrice;
            if (!isEtfDirectChart && beam.Etf == targetEtf && beam.ProjectedFuture > 0)
                return beam.ProjectedFuture;
            if (beam.EtfPrice > 0 && currentClose > 0 && latestEtfRefPrice > 0)
                return beam.EtfPrice * (currentClose / latestEtfRefPrice);
            return (beam.ProjectedFuture > 0) ? beam.ProjectedFuture : beam.EtfPrice;
        }

        private void EnsureRenderResources()
        {
            if (RenderTarget == null) return;

            if (dxDwFactory == null) dxDwFactory = new SharpDX.DirectWrite.Factory();
            if (dxFontMain == null) dxFontMain = new SharpDX.DirectWrite.TextFormat(dxDwFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.SemiBold, SharpDX.DirectWrite.FontStyle.Normal, 10.5f);
            if (dxFontSmall == null) dxFontSmall = new SharpDX.DirectWrite.TextFormat(dxDwFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Normal, SharpDX.DirectWrite.FontStyle.Normal, 9.5f);
            if (dxFontTitle == null) dxFontTitle = new SharpDX.DirectWrite.TextFormat(dxDwFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 11.0f);

            if (dxGradLilac == null)
            {
                SharpDX.Color baseCol = ToSharpColor(CorFeixePrincipal, 1.0f);
                SharpDX.Direct2D1.GradientStop[] stopsLilac = new SharpDX.Direct2D1.GradientStop[]
                {
                    new SharpDX.Direct2D1.GradientStop { Position = 0.00f, Color = new SharpDX.Color4(baseCol.R / 255f, baseCol.G / 255f, baseCol.B / 255f, 0.02f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 0.50f, Color = new SharpDX.Color4(baseCol.R / 255f, baseCol.G / 255f, baseCol.B / 255f, 0.28f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 0.90f, Color = new SharpDX.Color4(0.86f, 0.56f, 1.00f, 0.60f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 1.00f, Color = new SharpDX.Color4(0.97f, 0.85f, 1.00f, 0.78f) }
                };
                dxStopsLilac = new SharpDX.Direct2D1.GradientStopCollection(RenderTarget, stopsLilac);
                dxGradLilac = new SharpDX.Direct2D1.LinearGradientBrush(RenderTarget, new SharpDX.Direct2D1.LinearGradientBrushProperties
                {
                    StartPoint = new SharpDX.Vector2(0f, 0f),
                    EndPoint = new SharpDX.Vector2(200f, 0f)
                }, dxStopsLilac);

                SharpDX.Direct2D1.GradientStop[] stopsBid = new SharpDX.Direct2D1.GradientStop[]
                {
                    new SharpDX.Direct2D1.GradientStop { Position = 0.00f, Color = new SharpDX.Color4(0.45f, 0.25f, 0.90f, 0.02f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 0.55f, Color = new SharpDX.Color4(0.64f, 0.44f, 0.98f, 0.26f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 1.00f, Color = new SharpDX.Color4(0.16f, 0.92f, 0.64f, 0.65f) }
                };
                dxStopsBid = new SharpDX.Direct2D1.GradientStopCollection(RenderTarget, stopsBid);
                dxGradBid = new SharpDX.Direct2D1.LinearGradientBrush(RenderTarget, new SharpDX.Direct2D1.LinearGradientBrushProperties
                {
                    StartPoint = new SharpDX.Vector2(0f, 0f),
                    EndPoint = new SharpDX.Vector2(200f, 0f)
                }, dxStopsBid);

                SharpDX.Direct2D1.GradientStop[] stopsAsk = new SharpDX.Direct2D1.GradientStop[]
                {
                    new SharpDX.Direct2D1.GradientStop { Position = 0.00f, Color = new SharpDX.Color4(0.60f, 0.16f, 0.88f, 0.02f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 0.55f, Color = new SharpDX.Color4(0.84f, 0.26f, 0.95f, 0.28f) },
                    new SharpDX.Direct2D1.GradientStop { Position = 1.00f, Color = new SharpDX.Color4(0.98f, 0.30f, 0.55f, 0.66f) }
                };
                dxStopsAsk = new SharpDX.Direct2D1.GradientStopCollection(RenderTarget, stopsAsk);
                dxGradAsk = new SharpDX.Direct2D1.LinearGradientBrush(RenderTarget, new SharpDX.Direct2D1.LinearGradientBrushProperties
                {
                    StartPoint = new SharpDX.Vector2(0f, 0f),
                    EndPoint = new SharpDX.Vector2(200f, 0f)
                }, dxStopsAsk);
            }

            if (dxAuraLilac == null) dxAuraLilac = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.76f, 0.44f, 1.00f, 0.14f));
            if (dxAuraBid == null) dxAuraBid = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.20f, 0.90f, 0.62f, 0.14f));
            if (dxAuraAsk == null) dxAuraAsk = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.96f, 0.30f, 0.62f, 0.14f));

            if (dxCoreLilac == null) dxCoreLilac = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.90f, 0.68f, 1.00f, 0.92f));
            if (dxCoreBid == null) dxCoreBid = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.24f, 0.95f, 0.68f, 0.92f));
            if (dxCoreAsk == null) dxCoreAsk = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.98f, 0.34f, 0.60f, 0.92f));

            if (dxPillBg == null) dxPillBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.06f, 0.04f, 0.12f, 0.88f));
            if (dxPillBorder == null) dxPillBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.70f, 0.42f, 0.96f, 0.72f));
            if (dxTextBright == null) dxTextBright = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.97f, 0.95f, 1.00f, 0.98f));
            if (dxTextMuted == null) dxTextMuted = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.76f, 0.74f, 0.86f, 0.88f));
            if (dxBarTrack == null) dxBarTrack = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.18f, 0.16f, 0.28f, 0.85f));
            if (dxFinraCardBg == null) dxFinraCardBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.04f, 0.04f, 0.09f, 0.90f));
            if (dxLeader == null) dxLeader = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.78f, 0.56f, 1.00f, 0.55f));
        }

        private static SharpDX.Color ToSharpColor(System.Windows.Media.Brush wpfBrush, float alphaScale)
        {
            System.Windows.Media.SolidColorBrush scb = wpfBrush as System.Windows.Media.SolidColorBrush;
            if (scb == null) return new SharpDX.Color((byte)186, (byte)85, (byte)211, (byte)(255 * alphaScale));
            System.Windows.Media.Color c = scb.Color;
            return new SharpDX.Color(c.R, c.G, c.B, (byte)Math.Max(0, Math.Min(255, c.A * alphaScale)));
        }

        private static string FormatNotional(double m)
        {
            if (m >= 1000.0) return "$" + (m / 1000.0).ToString("0.00", CultureInfo.InvariantCulture) + "B";
            if (m >= 1.0) return "$" + m.ToString("0.0", CultureInfo.InvariantCulture) + "M";
            return "$" + (m * 1000.0).ToString("0", CultureInfo.InvariantCulture) + "K";
        }

        private static string FormatVolShort(double vol)
        {
            if (vol >= 1000000.0) return (vol / 1000000.0).ToString("0.00", CultureInfo.InvariantCulture) + "M";
            if (vol >= 1000.0) return (vol / 1000.0).ToString("0.0", CultureInfo.InvariantCulture) + "K";
            return vol.ToString("0", CultureInfo.InvariantCulture);
        }

        private float ResolveNonCollidingTop(float left, float desiredTop, float w, float h, float panelTop, float panelBottom)
        {
            float baseTop = Math.Max(panelTop + 4f, Math.Min(panelBottom - h - 4f, desiredTop - h * 0.5f));
            float[] offsets = new float[] { 0f, -18f, 18f, -36f, 36f, -54f, 54f };
            for (int i = 0; i < offsets.Length; i++)
            {
                float candTop = Math.Max(panelTop + 4f, Math.Min(panelBottom - h - 4f, baseTop + offsets[i]));
                bool collides = false;
                for (int j = 0; j < usedTagsScratch.Count; j++)
                {
                    SharpDX.RectangleF u = usedTagsScratch[j];
                    if (left - 2f < u.Right && left + w + 2f > u.Left && candTop - 1f < u.Bottom && candTop + h + 1f > u.Top)
                    {
                        collides = true;
                        break;
                    }
                }
                if (!collides)
                {
                    usedTagsScratch.Add(new SharpDX.RectangleF(left - 2f, candTop - 1f, w + 4f, h + 2f));
                    return candTop;
                }
            }
            usedTagsScratch.Add(new SharpDX.RectangleF(left - 2f, baseTop - 1f, w + 4f, h + 2f));
            return baseTop;
        }

        protected override void OnRender(ChartControl chartControl, ChartScale chartScale)
        {
            if (chartControl == null || chartScale == null || ChartBars == null || ChartPanel == null || RenderTarget == null)
                return;

            EnsureRenderResources();

            List<DpBeam> beamsSnapshot;
            FinraSummary finraSnap;
            string statusSnap;
            bool isOnSnap;
            lock (dataLock)
            {
                beamsSnapshot = new List<DpBeam>(activeBeams);
                finraSnap = finraSummary;
                statusSnap = feedStatusMsg;
                isOnSnap = apiOnline;
            }

            float panelLeft = (float)ChartPanel.X;
            float panelTop = (float)ChartPanel.Y;
            float panelRight = (float)(ChartPanel.X + ChartPanel.W);
            float panelBottom = (float)(ChartPanel.Y + ChartPanel.H);

            double currentPrice = (CurrentBar >= 0 && Close.Count > 0) ? Close[0] : 0.0;
            double tickSz = (TickSize > 0) ? TickSize : 0.25;

            int toIdx = ChartBars.ToIndex;
            float lastBarX = (toIdx >= 0) ? (float)chartControl.GetXByBarIndex(ChartBars, toIdx) : (panelRight - 90f);
            float barDist = (float)Math.Max(3.0, chartControl.Properties.BarDistance);
            float xEnd = Math.Max(panelLeft + 140f, Math.Min(panelRight - 10f, lastBarX + 26f));
            float xStart = Math.Max(panelLeft + 8f, xEnd - LarguraFeixeBarras * barDist);

            usedTagsScratch.Clear();
            int offscreenAbove = 0;
            int offscreenBelow = 0;

            AntialiasMode prevAa = RenderTarget.AntialiasMode;
            RenderTarget.AntialiasMode = AntialiasMode.PerPrimitive;

            for (int i = 0; i < beamsSnapshot.Count; i++)
            {
                DpBeam beam = beamsSnapshot[i];
                double levelPrice = ResolveChartLevel(beam, currentPrice);
                if (levelPrice <= 0) continue;

                float y = (float)chartScale.GetYByValue(levelPrice);
                if (y < panelTop + 8f) { offscreenAbove++; continue; }
                if (y > panelBottom - 8f) { offscreenBelow++; continue; }

                bool isBid = beam.SideBias.Contains("BID") || beam.SideBias.Contains("SUPPORT");
                bool isAsk = beam.SideBias.Contains("ASK") || beam.SideBias.Contains("RESIST");

                double scoreNorm = Math.Max(0.15, Math.Min(1.0, beam.AbsorptionScore / 100.0));
                bool isNear = (currentPrice > 0 && Math.Abs(levelPrice - currentPrice) <= DistanciaPulsoTicks * tickSz);
                bool shouldPulse = AtivarFeixePiscante && (isNear || beam.RvolBar >= 2.2 || beam.IsToday);
                float pulse = shouldPulse
                    ? (0.48f + 0.52f * (float)(0.5 + 0.5 * Math.Sin(Environment.TickCount * 0.0058 + i * 1.15)))
                    : 0.74f;

                SharpDX.Direct2D1.LinearGradientBrush gradBrush = isBid ? dxGradBid : (isAsk ? dxGradAsk : dxGradLilac);
                SharpDX.Direct2D1.SolidColorBrush auraBrush = isBid ? dxAuraBid : (isAsk ? dxAuraAsk : dxAuraLilac);
                SharpDX.Direct2D1.SolidColorBrush coreBrush = isBid ? dxCoreBid : (isAsk ? dxCoreAsk : dxCoreLilac);

                float auraHalfH = 5.5f + (float)(scoreNorm * 6.5) + (shouldPulse ? pulse * 1.8f : 0f);
                float bodyHalfH = 2.0f + (float)(scoreNorm * 2.2);

                // Camada 1: Feixe luminoso externo (Aura)
                auraBrush.Opacity = 0.25f * pulse;
                RenderTarget.FillRectangle(new SharpDX.RectangleF(xStart + 25f, y - auraHalfH, Math.Max(10f, xEnd - xStart - 25f), auraHalfH * 2f), auraBrush);

                // Camada 2: Degrade horizontal lilas (cauda suave -> ponta radiante)
                gradBrush.StartPoint = new SharpDX.Vector2(xStart, y);
                gradBrush.EndPoint = new SharpDX.Vector2(xEnd, y);
                gradBrush.Opacity = pulse;
                RenderTarget.FillRectangle(new SharpDX.RectangleF(xStart, y - bodyHalfH, Math.Max(10f, xEnd - xStart), bodyHalfH * 2f), gradBrush);

                // Camada 3: Filamento laser central + no radiante na ponta
                coreBrush.Opacity = Math.Min(1.0f, 0.65f + 0.35f * pulse);
                RenderTarget.DrawLine(new SharpDX.Vector2(xStart + 18f, y), new SharpDX.Vector2(xEnd, y), coreBrush, shouldPulse ? 1.65f : 1.15f);
                RenderTarget.FillEllipse(new SharpDX.Direct2D1.Ellipse(new SharpDX.Vector2(xEnd, y), 3.4f + pulse * 1.4f, 3.4f + pulse * 1.4f), coreBrush);

                // Camada 4: Etiqueta Dark Pool + Barra de Forca embutida
                string sideShort = isBid ? "BID SUP" : (isAsk ? "ASK ABS" : "CLUSTER");
                string timeTag = !string.IsNullOrEmpty(beam.TimeBrt) ? beam.TimeBrt : beam.TimeEt;
                string priceTag = (Instrument != null && Instrument.MasterInstrument != null)
                    ? Instrument.MasterInstrument.FormatPrice(Instrument.MasterInstrument.RoundToTickSize(levelPrice))
                    : levelPrice.ToString("0.##", CultureInfo.InvariantCulture);
                string tagText = "DP " + beam.Etf + " @ " + priceTag + " · " + FormatNotional(beam.NotionalM) + " · " + FormatVolShort(beam.BarVolume) + " · " + sideShort;
                if (!string.IsNullOrEmpty(timeTag)) tagText += " · " + timeTag;

                float pillW = Math.Max(160f, tagText.Length * 5.65f + 22f);
                float pillH = 20f;
                float pillLeft = Math.Max(panelLeft + 6f, Math.Min(panelRight - pillW - 10f, xEnd - pillW - 10f));
                float pillTop = ResolveNonCollidingTop(pillLeft, y, pillW, pillH, panelTop, panelBottom);

                float midY = pillTop + pillH * 0.5f;
                if (Math.Abs(midY - y) > 3f)
                    RenderTarget.DrawLine(new SharpDX.Vector2(pillLeft + pillW, midY), new SharpDX.Vector2(xEnd, y), dxLeader, 0.85f);

                SharpDX.RectangleF tagRect = new SharpDX.RectangleF(pillLeft, pillTop, pillW, pillH);
                SharpDX.Direct2D1.RoundedRectangle roundedPill = new SharpDX.Direct2D1.RoundedRectangle { Rect = tagRect, RadiusX = 4f, RadiusY = 4f };
                RenderTarget.FillRoundedRectangle(roundedPill, dxPillBg);
                RenderTarget.DrawRoundedRectangle(roundedPill, coreBrush, shouldPulse ? 1.1f : 0.7f);

                // Faixa lateral + Barra de Forca no rodape da pilula
                RenderTarget.FillRectangle(new SharpDX.RectangleF(pillLeft + 2.5f, pillTop + 3f, 3f, pillH - 6f), coreBrush);
                RenderTarget.DrawText(tagText, dxFontSmall, new SharpDX.RectangleF(pillLeft + 9f, pillTop + 1.5f, pillW - 14f, 13f), dxTextBright);

                float barTrackW = pillW - 14f;
                float barFillW = Math.Max(4f, barTrackW * (float)scoreNorm);
                RenderTarget.FillRectangle(new SharpDX.RectangleF(pillLeft + 9f, pillTop + pillH - 4.5f, barTrackW, 2.2f), dxBarTrack);
                RenderTarget.FillRectangle(new SharpDX.RectangleF(pillLeft + 9f, pillTop + pillH - 4.5f, barFillW, 2.2f), coreBrush);
            }

            // Card Resumo FINRA + Barra de Forca Dark Pool (canto inferior esquerdo)
            if (MostrarBarraFinra)
            {
                float cardW = finraSnap.HasData ? 310f : 380f;
                float cardH = finraSnap.HasData ? 76f : 62f;
                float cardLeft = panelLeft + 10f;
                float cardTop = Math.Max(panelTop + 10f, panelBottom - cardH - 12f);

                SharpDX.RectangleF cardRect = new SharpDX.RectangleF(cardLeft, cardTop, cardW, cardH);
                SharpDX.Direct2D1.RoundedRectangle rrCard = new SharpDX.Direct2D1.RoundedRectangle { Rect = cardRect, RadiusX = 6f, RadiusY = 6f };
                RenderTarget.FillRoundedRectangle(rrCard, dxFinraCardBg);
                RenderTarget.DrawRoundedRectangle(rrCard, dxPillBorder, 1.0f);

                string dot = isOnSnap ? "ON" : "OFF";
                string titleLine = "VELTRIX DARK POOL · " + targetDisplay + " (" + targetEtf + ") [" + dot + "]";
                RenderTarget.DrawText(titleLine, dxFontTitle, new SharpDX.RectangleF(cardLeft + 10f, cardTop + 6f, cardW - 20f, 16f), isOnSnap ? dxTextBright : dxCoreAsk);

                if (finraSnap.HasData)
                {
                    double buyPct = Math.Max(0.0, Math.Min(100.0, finraSnap.NonShortPct));
                    double sellPct = Math.Max(0.0, Math.Min(100.0, finraSnap.ShortPct));
                    string finraInfo = "FINRA " + finraSnap.Date + " · " + FormatNotional(finraSnap.NotionalM) + " · " + finraSnap.FlowTag;
                    RenderTarget.DrawText(finraInfo, dxFontSmall, new SharpDX.RectangleF(cardLeft + 10f, cardTop + 23f, cardW - 20f, 14f), dxTextMuted);

                    float meterX = cardLeft + 10f;
                    float meterY = cardTop + 40f;
                    float meterW = cardW - 20f;
                    float buyW = (float)(meterW * (buyPct / 100.0));
                    RenderTarget.FillRectangle(new SharpDX.RectangleF(meterX, meterY, meterW, 7f), dxCoreAsk);
                    RenderTarget.FillRectangle(new SharpDX.RectangleF(meterX, meterY, buyW, 7f), dxCoreBid);

                    string meterText = "COMPRA/NON-SHORT: " + buyPct.ToString("0.0", CultureInfo.InvariantCulture) + "%   |   SHORT: " + sellPct.ToString("0.0", CultureInfo.InvariantCulture) + "%";
                    if (offscreenAbove > 0 || offscreenBelow > 0)
                        meterText += "   (+" + offscreenAbove + "^ / -" + offscreenBelow + "v)";
                    RenderTarget.DrawText(meterText, dxFontSmall, new SharpDX.RectangleF(cardLeft + 10f, cardTop + 52f, cardW - 20f, 15f), dxTextBright);
                }
                else
                {
                    string sub = statusSnap + " · " + resolvedUrlInUse;
                    RenderTarget.DrawText(sub, dxFontSmall, new SharpDX.RectangleF(cardLeft + 10f, cardTop + 25f, cardW - 20f, cardH - 30f), dxTextMuted);
                }
            }

            RenderTarget.AntialiasMode = prevAa;
        }

        private void LimparRecursosRender()
        {
            if (dxGradLilac != null) { dxGradLilac.Dispose(); dxGradLilac = null; }
            if (dxGradBid != null) { dxGradBid.Dispose(); dxGradBid = null; }
            if (dxGradAsk != null) { dxGradAsk.Dispose(); dxGradAsk = null; }
            if (dxStopsLilac != null) { dxStopsLilac.Dispose(); dxStopsLilac = null; }
            if (dxStopsBid != null) { dxStopsBid.Dispose(); dxStopsBid = null; }
            if (dxStopsAsk != null) { dxStopsAsk.Dispose(); dxStopsAsk = null; }

            if (dxAuraLilac != null) { dxAuraLilac.Dispose(); dxAuraLilac = null; }
            if (dxAuraBid != null) { dxAuraBid.Dispose(); dxAuraBid = null; }
            if (dxAuraAsk != null) { dxAuraAsk.Dispose(); dxAuraAsk = null; }
            if (dxCoreLilac != null) { dxCoreLilac.Dispose(); dxCoreLilac = null; }
            if (dxCoreBid != null) { dxCoreBid.Dispose(); dxCoreBid = null; }
            if (dxCoreAsk != null) { dxCoreAsk.Dispose(); dxCoreAsk = null; }
            if (dxPillBg != null) { dxPillBg.Dispose(); dxPillBg = null; }
            if (dxPillBorder != null) { dxPillBorder.Dispose(); dxPillBorder = null; }
            if (dxTextBright != null) { dxTextBright.Dispose(); dxTextBright = null; }
            if (dxTextMuted != null) { dxTextMuted.Dispose(); dxTextMuted = null; }
            if (dxBarTrack != null) { dxBarTrack.Dispose(); dxBarTrack = null; }
            if (dxFinraCardBg != null) { dxFinraCardBg.Dispose(); dxFinraCardBg = null; }
            if (dxLeader != null) { dxLeader.Dispose(); dxLeader = null; }
            if (dxFontMain != null) { dxFontMain.Dispose(); dxFontMain = null; }
            if (dxFontSmall != null) { dxFontSmall.Dispose(); dxFontSmall = null; }
            if (dxFontTitle != null) { dxFontTitle.Dispose(); dxFontTitle = null; }
            if (dxDwFactory != null) { dxDwFactory.Dispose(); dxDwFactory = null; }
        }

        public override void OnRenderTargetChanged()
        {
            LimparRecursosRender();
        }
    }
}
'''

# ==============================================================================
# 12. NYSE TICK BREADTH PRO (MODO A AUTOMATICO: FEED NATIVO + PROXY CESTA ~15s)
# ==============================================================================
CODE_NYSE_TICK_BREADTH = r'''using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using System.Net;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.NinjaScript;
using SharpDX;
using SharpDX.Direct2D1;
using SharpDX.DirectWrite;

namespace NinjaTrader.NinjaScript.Indicators
{
    public class NyseTickBreadthPro : Indicator
    {
        private class MacroCorrItem
        {
            public string Id;
            public double Price;
            public double ChangePct;
            public double CorrEs;
            public double CorrNq;
            public string CorrelationType;
        }

        private sealed class VeltrixTimeoutWebClient : WebClient
        {
            private readonly int timeoutMs;
            public VeltrixTimeoutWebClient(int timeoutMs) { this.timeoutMs = timeoutMs; }

            protected override WebRequest GetWebRequest(Uri address)
            {
                ServicePointManager.SecurityProtocol |= (SecurityProtocolType)3072 | (SecurityProtocolType)768 | SecurityProtocolType.Tls;
                WebRequest req = base.GetWebRequest(address);
                if (req != null) req.Timeout = timeoutMs;
                HttpWebRequest http = req as HttpWebRequest;
                if (http != null)
                {
                    http.UserAgent = "VeltrixQuant-NT8/1.0";
                    http.AutomaticDecompression = DecompressionMethods.GZip | DecompressionMethods.Deflate;
                }
                return req;
            }
        }

        private sealed class VeltrixJsonParser
        {
            private readonly string json;
            private int idx;
            private VeltrixJsonParser(string src) { json = src ?? ""; idx = 0; }

            public static object Parse(string src)
            {
                if (string.IsNullOrEmpty(src)) return null;
                VeltrixJsonParser p = new VeltrixJsonParser(src);
                return p.ParseValue();
            }

            private void SkipWs() { while (idx < json.Length && char.IsWhiteSpace(json[idx])) idx++; }

            private object ParseValue()
            {
                SkipWs();
                if (idx >= json.Length) return null;
                char c = json[idx];
                if (c == '{') return ParseObject();
                if (c == '[') return ParseArray();
                if (c == '"') return ParseString();
                if (c == 't') { idx += 4; return true; }
                if (c == 'f') { idx += 5; return false; }
                if (c == 'n') { idx += 4; return null; }
                return ParseNumber();
            }

            private Dictionary<string, object> ParseObject()
            {
                Dictionary<string, object> map = new Dictionary<string, object>(StringComparer.OrdinalIgnoreCase);
                idx++;
                while (idx < json.Length)
                {
                    SkipWs();
                    if (idx >= json.Length) break;
                    if (json[idx] == '}') { idx++; break; }
                    if (json[idx] == ',') { idx++; continue; }
                    string key = ParseString();
                    SkipWs();
                    if (idx < json.Length && json[idx] == ':') idx++;
                    object val = ParseValue();
                    if (key != null) map[key] = val;
                }
                return map;
            }

            private List<object> ParseArray()
            {
                List<object> list = new List<object>();
                idx++;
                while (idx < json.Length)
                {
                    SkipWs();
                    if (idx >= json.Length) break;
                    if (json[idx] == ']') { idx++; break; }
                    if (json[idx] == ',') { idx++; continue; }
                    list.Add(ParseValue());
                }
                return list;
            }

            private string ParseString()
            {
                if (idx >= json.Length || json[idx] != '"') return string.Empty;
                idx++;
                StringBuilder sb = new StringBuilder();
                while (idx < json.Length)
                {
                    char c = json[idx++];
                    if (c == '"') break;
                    if (c == '\\' && idx < json.Length)
                    {
                        char esc = json[idx++];
                        switch (esc)
                        {
                            case '"': sb.Append('"'); break;
                            case '\\': sb.Append('\\'); break;
                            case '/': sb.Append('/'); break;
                            case 'b': sb.Append('\b'); break;
                            case 'f': sb.Append('\f'); break;
                            case 'n': sb.Append('\n'); break;
                            case 'r': sb.Append('\r'); break;
                            case 't': sb.Append('\t'); break;
                            case 'u':
                                if (idx + 4 <= json.Length)
                                {
                                    int hex;
                                    if (int.TryParse(json.Substring(idx, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out hex))
                                        sb.Append((char)hex);
                                    idx += 4;
                                }
                                break;
                            default: sb.Append(esc); break;
                        }
                    }
                    else sb.Append(c);
                }
                return sb.ToString();
            }

            private object ParseNumber()
            {
                int start = idx;
                while (idx < json.Length)
                {
                    char c = json[idx];
                    if ((c >= '0' && c <= '9') || c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E') idx++;
                    else break;
                }
                string token = json.Substring(start, Math.Max(0, idx - start));
                double num;
                if (double.TryParse(token, NumberStyles.Any, CultureInfo.InvariantCulture, out num)) return num;
                return 0.0;
            }

            public static Dictionary<string, object> AsDict(object obj) { return obj as Dictionary<string, object>; }
            public static List<object> AsList(object obj) { return obj as List<object>; }

            public static string Str(Dictionary<string, object> d, string key, string defVal)
            {
                if (d == null) return defVal;
                object v;
                if (!d.TryGetValue(key, out v) || v == null) return defVal;
                return Convert.ToString(v, CultureInfo.InvariantCulture) ?? defVal;
            }

            public static double Num(Dictionary<string, object> d, string key, double defVal)
            {
                if (d == null) return defVal;
                object v;
                if (!d.TryGetValue(key, out v) || v == null) return defVal;
                if (v is double) return (double)v;
                if (v is int) return (int)v;
                double parsed;
                if (double.TryParse(Convert.ToString(v, CultureInfo.InvariantCulture), NumberStyles.Any, CultureInfo.InvariantCulture, out parsed))
                    return parsed;
                return defVal;
            }

            public static bool Bool(Dictionary<string, object> d, string key, bool defVal)
            {
                if (d == null) return defVal;
                object v;
                if (!d.TryGetValue(key, out v) || v == null) return defVal;
                if (v is bool) return (bool)v;
                return defVal;
            }
        }

        private readonly object syncLock = new object();
        private int nativeSeriesIndex = -1;
        private string nativeSymbol = string.Empty;
        private double lastNativeTick = 0.0;
        private DateTime lastNativeUtc = DateTime.MinValue;

        private double apiTickValue = 0.0;
        private double apiTickqValue = 0.0;
        private double apiAddValue = 0.0;
        private double apiVixValue = 0.0;
        private double apiVixChg = 0.0;
        private bool apiOnline = false;
        private string apiFeedLabel = "MODO B PENDENTE";
        private List<MacroCorrItem> macroCorrList = new List<MacroCorrItem>();
        private string chartRoot = "ES";

        private Timer pollTimer;
        private int isFetching = 0;

        private SharpDX.Direct2D1.SolidColorBrush dxZoneBull;
        private SharpDX.Direct2D1.SolidColorBrush dxZoneBear;
        private SharpDX.Direct2D1.SolidColorBrush dxBandBg;
        private SharpDX.Direct2D1.SolidColorBrush dxBorder;
        private SharpDX.Direct2D1.SolidColorBrush dxTextLight;
        private SharpDX.Direct2D1.SolidColorBrush dxTextMuted;
        private SharpDX.Direct2D1.SolidColorBrush dxBullBrush;
        private SharpDX.Direct2D1.SolidColorBrush dxBearBrush;
        private SharpDX.Direct2D1.SolidColorBrush dxModoABrush;
        private SharpDX.Direct2D1.SolidColorBrush dxModoBBrush;
        private SharpDX.DirectWrite.Factory dxDwFactory;
        private SharpDX.DirectWrite.TextFormat dxFontTitle;
        private SharpDX.DirectWrite.TextFormat dxFontSmall;

        #region Propriedades
        [NinjaScriptProperty]
        [Display(Name = "URL Dashboard (AUTO ou URL)", Order = 1, GroupName = "01. Modo A Automatico")]
        public string DashboardUrl { get; set; }

        [NinjaScriptProperty]
        [Range(5, 180)]
        [Display(Name = "Atualizar Modo B (Segundos)", Order = 2, GroupName = "01. Modo A Automatico")]
        public int AtualizarSegundos { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Modo A: Preferir Feed Nativo NT8", Description = "Usa $TICK/^TICK/TICK.Z automaticamente se disponivel; senao usa API Proxy.", Order = 3, GroupName = "01. Modo A Automatico")]
        public bool PreferirFeedNativo { get; set; }

        [NinjaScriptProperty]
        [Range(200, 1500)]
        [Display(Name = "Nivel Alerta Alto (+ / -)", Order = 4, GroupName = "02. Limiares Breadth")]
        public double NivelAlertaAlto { get; set; }

        [NinjaScriptProperty]
        [Range(500, 2200)]
        [Display(Name = "Nivel Climax Extremo (+ / -)", Order = 5, GroupName = "02. Limiares Breadth")]
        public double NivelClimax { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Mostrar Correlacao do Ativo no Painel", Order = 6, GroupName = "03. Visual")]
        public bool MostrarCorrelacaoAtivo { get; set; }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "Cor Compra Forte", Order = 7, GroupName = "03. Visual")]
        public System.Windows.Media.Brush CorCompraForte { get; set; }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "Cor Compra Climax", Order = 8, GroupName = "03. Visual")]
        public System.Windows.Media.Brush CorCompraExtrema { get; set; }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "Cor Venda Forte", Order = 9, GroupName = "03. Visual")]
        public System.Windows.Media.Brush CorVendaForte { get; set; }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "Cor Venda Climax", Order = 10, GroupName = "03. Visual")]
        public System.Windows.Media.Brush CorVendaExtrema { get; set; }

        [NinjaScriptProperty]
        [XmlIgnore]
        [Display(Name = "Cor Neutra", Order = 11, GroupName = "03. Visual")]
        public System.Windows.Media.Brush CorNeutra { get; set; }

        [Browsable(false)] public string CorCompraForteS { get { return Serialize.BrushToString(CorCompraForte); } set { CorCompraForte = Serialize.StringToBrush(value); } }
        [Browsable(false)] public string CorCompraExtremaS { get { return Serialize.BrushToString(CorCompraExtrema); } set { CorCompraExtrema = Serialize.StringToBrush(value); } }
        [Browsable(false)] public string CorVendaForteS { get { return Serialize.BrushToString(CorVendaForte); } set { CorVendaForte = Serialize.StringToBrush(value); } }
        [Browsable(false)] public string CorVendaExtremaS { get { return Serialize.BrushToString(CorVendaExtrema); } set { CorVendaExtrema = Serialize.StringToBrush(value); } }
        [Browsable(false)] public string CorNeutraS { get { return Serialize.BrushToString(CorNeutra); } set { CorNeutra = Serialize.StringToBrush(value); } }
        #endregion

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "NYSE $TICK Hibrido Modo A Automatico: detecta IQFeed/Kinetick nativo no NT8 e alterna sem falhas para API Proxy + Correlacao.";
                Name = "VeltrixQuant - NyseTickBreadthPro";
                Calculate = Calculate.OnEachTick;
                IsOverlay = false;
                DrawOnPricePanel = false;
                IsAutoScale = true;
                IsSuspendedWhileInactive = true;

                DashboardUrl = "AUTO";
                AtualizarSegundos = 15;
                PreferirFeedNativo = true;
                NivelAlertaAlto = 800;
                NivelClimax = 1000;
                MostrarCorrelacaoAtivo = true;

                CorCompraForte = Brushes.LimeGreen;
                CorCompraExtrema = Brushes.SpringGreen;
                CorVendaForte = Brushes.Crimson;
                CorVendaExtrema = Brushes.Magenta;
                CorNeutra = Brushes.SlateGray;

                AddPlot(new Stroke(Brushes.DeepSkyBlue, 2), PlotStyle.Bar, "NyseTickValue");
                AddLine(new Stroke(Brushes.DimGray, DashStyleHelper.Dot, 1), 0, "Zero");
                AddLine(new Stroke(Brushes.ForestGreen, DashStyleHelper.Dash, 1), 800, "ExtremeHigh");
                AddLine(new Stroke(Brushes.Firebrick, DashStyleHelper.Dash, 1), -800, "ExtremeLow");
            }
            else if (State == State.Configure)
            {
                if (PreferirFeedNativo)
                {
                    bool hasIqFeed = DetectIqFeedConnection();
                    string[] candidates = hasIqFeed
                        ? new string[] { "TICK.Z", "^TICK", "$TICK", "TICK-NYSE" }
                        : new string[] { "^TICK", "$TICK", "TICK.Z", "TICK-NYSE" };

                    for (int i = 0; i < candidates.Length; i++)
                    {
                        try
                        {
                            NinjaTrader.Cbi.Instrument inst = NinjaTrader.Cbi.Instrument.GetInstrument(candidates[i]);
                            if (inst != null)
                            {
                                AddDataSeries(candidates[i], BarsPeriodType.Minute, 1);
                                nativeSeriesIndex = 1;
                                nativeSymbol = candidates[i];
                                break;
                            }
                        }
                        catch { }
                    }
                }
            }
            else if (State == State.DataLoaded)
            {
                string raw = (Instrument != null && Instrument.MasterInstrument != null && !string.IsNullOrEmpty(Instrument.MasterInstrument.Name))
                    ? Instrument.MasterInstrument.Name.Trim().ToUpperInvariant() : "ES";
                string[] parts = raw.Split(new char[] { ' ', '-', '.', '/' }, StringSplitOptions.RemoveEmptyEntries);
                chartRoot = (parts.Length > 0) ? parts[0] : raw;

                int ms = Math.Max(5000, AtualizarSegundos * 1000);
                pollTimer = new Timer(_ => PollMarketContext(), null, 300, ms);
            }
            else if (State == State.Terminated)
            {
                try { if (pollTimer != null) { pollTimer.Dispose(); pollTimer = null; } } catch { }
                LimparRecursosRender();
            }
        }

        private bool DetectIqFeedConnection()
        {
            try
            {
                Type connType = typeof(NinjaTrader.Cbi.Connection);
                PropertyInfo connsProp = connType.GetProperty("Connections", BindingFlags.Public | BindingFlags.Static);
                if (connsProp == null) return false;
                IEnumerable conns = connsProp.GetValue(null, null) as IEnumerable;
                if (conns == null) return false;
                foreach (object c in conns)
                {
                    if (c == null) continue;
                    string s = c.ToString();
                    if (s.IndexOf("IQFeed", StringComparison.OrdinalIgnoreCase) >= 0) return true;
                    PropertyInfo optProp = c.GetType().GetProperty("Options");
                    if (optProp != null)
                    {
                        object opt = optProp.GetValue(c, null);
                        if (opt != null && opt.ToString().IndexOf("IQFeed", StringComparison.OrdinalIgnoreCase) >= 0)
                            return true;
                    }
                }
            }
            catch { }
            return false;
        }

        private string ResolveDashboardBaseUrl()
        {
            string manual = (DashboardUrl ?? string.Empty).Trim();
            if (!string.IsNullOrEmpty(manual) && !string.Equals(manual, "AUTO", StringComparison.OrdinalIgnoreCase))
                return manual.TrimEnd('/');
            try
            {
                string envUrl = Environment.GetEnvironmentVariable("VELTRIX_DASHBOARD_URL");
                if (!string.IsNullOrEmpty(envUrl)) return envUrl.Trim().TrimEnd('/');
                string docs = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                string[] cfgPaths = new string[]
                {
                    Path.Combine(docs, "NinjaTrader 8", "bin", "Custom", "Indicators", "VeltrixQuant", "VeltrixQuant_URL.txt"),
                    Path.Combine(docs, "NinjaTrader 8", "VeltrixQuant_URL.txt"),
                    Path.Combine(docs, "VeltrixQuant_URL.txt")
                };
                for (int i = 0; i < cfgPaths.Length; i++)
                {
                    if (File.Exists(cfgPaths[i]))
                    {
                        string fileUrl = File.ReadAllText(cfgPaths[i]).Trim();
                        if (!string.IsNullOrEmpty(fileUrl) && fileUrl.StartsWith("http", StringComparison.OrdinalIgnoreCase))
                            return fileUrl.TrimEnd('/');
                    }
                }
            }
            catch { }
            return "https://gex-dashboard-git-master-gex-cloud.vercel.app";
        }

        private string ResolveVercelBypassToken()
        {
            try
            {
                string envTok = Environment.GetEnvironmentVariable("VELTRIX_BYPASS_TOKEN");
                if (!string.IsNullOrEmpty(envTok)) return envTok.Trim();

                string docs = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                string[] tokPaths = new string[]
                {
                    Path.Combine(docs, "NinjaTrader 8", "bin", "Custom", "Indicators", "VeltrixQuant", "VeltrixQuant_BYPASS.txt"),
                    Path.Combine(docs, "NinjaTrader 8", "VeltrixQuant_BYPASS.txt"),
                    Path.Combine(docs, "VeltrixQuant_BYPASS.txt")
                };
                for (int i = 0; i < tokPaths.Length; i++)
                {
                    if (File.Exists(tokPaths[i]))
                    {
                        string tok = File.ReadAllText(tokPaths[i]).Trim();
                        if (!string.IsNullOrEmpty(tok)) return tok;
                    }
                }
            }
            catch { }
            return string.Empty;
        }

        private void PollMarketContext()
        {
            if (State == State.Terminated) return;
            if (Interlocked.CompareExchange(ref isFetching, 1, 0) != 0) return;
            try
            {
                string primaryUrl = ResolveDashboardBaseUrl();
                string bypassToken = ResolveVercelBypassToken();
                List<string> candList = new List<string>();
                candList.Add(primaryUrl);
                if (!candList.Exists(u => string.Equals(u, "http://localhost:3000", StringComparison.OrdinalIgnoreCase)))
                    candList.Add("http://localhost:3000");
                if (!candList.Exists(u => string.Equals(u, "http://127.0.0.1:3000", StringComparison.OrdinalIgnoreCase)))
                    candList.Add("http://127.0.0.1:3000");

                try { ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12; } catch { }

                Dictionary<string, object> root = null;
                List<object> assets = null;
                bool htmlBlocked = false;
                Exception lastEx = null;

                for (int c = 0; c < candList.Count; c++)
                {
                    string url = candList[c] + "/api/market-context";
                    try
                    {
                        string payload;
                        using (VeltrixTimeoutWebClient wc = new VeltrixTimeoutWebClient(20000))
                        {
                            wc.Encoding = Encoding.UTF8;
                            if (!string.IsNullOrEmpty(bypassToken) && candList[c].IndexOf("vercel.app", StringComparison.OrdinalIgnoreCase) >= 0)
                                wc.Headers["x-vercel-protection-bypass"] = bypassToken;
                            payload = wc.DownloadString(url);
                        }

                        if (!string.IsNullOrEmpty(payload) && payload.TrimStart().StartsWith("<", StringComparison.Ordinal))
                        {
                            htmlBlocked = true;
                            continue;
                        }

                        root = VeltrixJsonParser.AsDict(VeltrixJsonParser.Parse(payload));
                        assets = (root != null) ? VeltrixJsonParser.AsList(root.ContainsKey("assets") ? root["assets"] : null) : null;
                        if (assets != null)
                        {
                            lastEx = null;
                            break;
                        }
                    }
                    catch (Exception ex)
                    {
                        lastEx = ex;
                    }
                }

                if (assets == null)
                {
                    lock (syncLock)
                    {
                        apiOnline = false;
                        apiFeedLabel = htmlBlocked
                            ? "VERCEL EXIGE LOGIN"
                            : (lastEx != null ? "API OFFLINE" : "SEM ASSETS");
                    }
                    if (ChartControl != null)
                    {
                        ChartControl.Dispatcher.InvokeAsync(new Action(() =>
                        {
                            if (ChartControl != null && State != State.Terminated) ChartControl.InvalidateVisual();
                        }));
                    }
                    return;
                }

                double tickP = 0, tickqP = 0, addP = 0, vixP = 0, vixC = 0;
                List<MacroCorrItem> list = new List<MacroCorrItem>();
                for (int i = 0; i < assets.Count; i++)
                {
                    Dictionary<string, object> a = VeltrixJsonParser.AsDict(assets[i]);
                    if (a == null) continue;
                    string id = VeltrixJsonParser.Str(a, "id", string.Empty).ToUpperInvariant();
                    double price = VeltrixJsonParser.Num(a, "price", 0.0);
                    double chg = VeltrixJsonParser.Num(a, "changePct", 0.0);
                    double corrEs = VeltrixJsonParser.Num(a, "realizedCorrES", VeltrixJsonParser.Num(a, "expectedCorrES", 0.0));
                    double corrNq = VeltrixJsonParser.Num(a, "realizedCorrNQ", VeltrixJsonParser.Num(a, "expectedCorrNQ", 0.0));
                    string cType = VeltrixJsonParser.Str(a, "correlationType", string.Empty);

                    if (id == "TICK") tickP = price;
                    else if (id == "TICKQ") tickqP = price;
                    else if (id == "ADD") addP = price;
                    else if (id == "VIX") { vixP = price; vixC = chg; }

                    if (id == "VIX" || id == "ZN" || id == "ZB" || id == "DXY" || id == "HYG" || id == "GC" || id == "CL" || id == "ES" || id == "NQ")
                    {
                        list.Add(new MacroCorrItem { Id = id, Price = price, ChangePct = chg, CorrEs = corrEs, CorrNq = corrNq, CorrelationType = cType });
                    }
                }

                lock (syncLock)
                {
                    apiTickValue = tickP;
                    apiTickqValue = tickqP;
                    apiAddValue = addP;
                    apiVixValue = vixP;
                    apiVixChg = vixC;
                    macroCorrList = list;
                    apiOnline = true;
                    apiFeedLabel = VeltrixJsonParser.Str(root, "feedStatus", "PROXY WEB");
                }

                if (ChartControl != null)
                {
                    ChartControl.Dispatcher.InvokeAsync(new Action(() =>
                    {
                        if (ChartControl != null && State != State.Terminated) ChartControl.InvalidateVisual();
                    }));
                }
            }
            catch
            {
                lock (syncLock) { apiOnline = false; }
            }
            finally
            {
                Interlocked.Exchange(ref isFetching, 0);
            }
        }

        private bool IsModoAActiveNow()
        {
            if (!PreferirFeedNativo || nativeSeriesIndex <= 0) return false;
            if (CurrentBars.Length <= nativeSeriesIndex || CurrentBars[nativeSeriesIndex] < 0) return false;
            if (lastNativeTick == 0.0) return false;
            if (State == State.Realtime && apiOnline && lastNativeUtc != DateTime.MinValue)
            {
                if ((DateTime.UtcNow - lastNativeUtc).TotalMinutes > 12.0 && apiTickValue != 0.0)
                    return false;
            }
            return true;
        }

        protected override void OnBarUpdate()
        {
            if (nativeSeriesIndex > 0 && BarsInProgress == nativeSeriesIndex)
            {
                if (CurrentBars[nativeSeriesIndex] >= 0)
                {
                    lastNativeTick = Closes[nativeSeriesIndex][0];
                    if (State == State.Realtime) lastNativeUtc = DateTime.UtcNow;
                }
                return;
            }

            if (BarsInProgress != 0 || CurrentBar < 0) return;

            double val;
            lock (syncLock)
            {
                val = IsModoAActiveNow() ? lastNativeTick : apiTickValue;
            }

            if (val > 3000.0) val = 3000.0;
            if (val < -3000.0) val = -3000.0;
            Values[0][0] = val;

            if (val >= NivelClimax) PlotBrushes[0][0] = CorCompraExtrema;
            else if (val >= NivelAlertaAlto) PlotBrushes[0][0] = CorCompraForte;
            else if (val <= -NivelClimax) PlotBrushes[0][0] = CorVendaExtrema;
            else if (val <= -NivelAlertaAlto) PlotBrushes[0][0] = CorVendaForte;
            else if (val > 200) PlotBrushes[0][0] = Brushes.MediumAquamarine;
            else if (val < -200) PlotBrushes[0][0] = Brushes.IndianRed;
            else PlotBrushes[0][0] = CorNeutra;
        }

        private void EnsureRenderResources()
        {
            if (RenderTarget == null) return;
            if (dxDwFactory == null) dxDwFactory = new SharpDX.DirectWrite.Factory();
            if (dxFontTitle == null) dxFontTitle = new SharpDX.DirectWrite.TextFormat(dxDwFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 11.0f);
            if (dxFontSmall == null) dxFontSmall = new SharpDX.DirectWrite.TextFormat(dxDwFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Normal, SharpDX.DirectWrite.FontStyle.Normal, 9.5f);

            if (dxZoneBull == null) dxZoneBull = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.10f, 0.85f, 0.45f, 0.08f));
            if (dxZoneBear == null) dxZoneBear = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.95f, 0.22f, 0.38f, 0.08f));
            if (dxBandBg == null) dxBandBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.05f, 0.05f, 0.11f, 0.86f));
            if (dxBorder == null) dxBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.32f, 0.45f, 0.72f, 0.65f));
            if (dxTextLight == null) dxTextLight = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.96f, 0.97f, 1.00f, 0.96f));
            if (dxTextMuted == null) dxTextMuted = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.70f, 0.76f, 0.88f, 0.90f));
            if (dxBullBrush == null) dxBullBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.22f, 0.95f, 0.56f, 0.95f));
            if (dxBearBrush == null) dxBearBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.98f, 0.30f, 0.48f, 0.95f));
            if (dxModoABrush == null) dxModoABrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.20f, 0.92f, 0.65f, 0.96f));
            if (dxModoBBrush == null) dxModoBBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.78f, 0.52f, 1.00f, 0.96f));
        }

        protected override void OnRender(ChartControl chartControl, ChartScale chartScale)
        {
            base.OnRender(chartControl, chartScale);
            if (chartControl == null || chartScale == null || ChartPanel == null || RenderTarget == null) return;
            EnsureRenderResources();

            float panelLeft = (float)ChartPanel.X;
            float panelTop = (float)ChartPanel.Y;
            float panelRight = (float)(ChartPanel.X + ChartPanel.W);
            float panelBottom = (float)(ChartPanel.Y + ChartPanel.H);

            // Faixas visuais de Climax (+1000 / -1000)
            float yPlus = (float)chartScale.GetYByValue(NivelClimax);
            float yMinus = (float)chartScale.GetYByValue(-NivelClimax);
            if (yPlus > panelTop && yPlus < panelBottom)
                RenderTarget.FillRectangle(new SharpDX.RectangleF(panelLeft, panelTop, panelRight - panelLeft, yPlus - panelTop), dxZoneBull);
            if (yMinus > panelTop && yMinus < panelBottom)
                RenderTarget.FillRectangle(new SharpDX.RectangleF(panelLeft, yMinus, panelRight - panelLeft, panelBottom - yMinus), dxZoneBear);

            bool modoA;
            double curTick, tq, addV, vixV, vixC;
            bool isOn;
            List<MacroCorrItem> corrSnap;
            lock (syncLock)
            {
                modoA = IsModoAActiveNow();
                curTick = modoA ? lastNativeTick : apiTickValue;
                tq = apiTickqValue;
                addV = apiAddValue;
                vixV = apiVixValue;
                vixC = apiVixChg;
                isOn = apiOnline;
                corrSnap = new List<MacroCorrItem>(macroCorrList);
            }

            float hudTop = panelTop + 24f;
            float hudW = Math.Min(panelRight - panelLeft - 16f, 520f);
            float hudH = MostrarCorrelacaoAtivo ? 42f : 24f;
            SharpDX.RectangleF hudRect = new SharpDX.RectangleF(panelLeft + 8f, hudTop, hudW, hudH);
            SharpDX.Direct2D1.RoundedRectangle rr = new SharpDX.Direct2D1.RoundedRectangle { Rect = hudRect, RadiusX = 4f, RadiusY = 4f };
            RenderTarget.FillRoundedRectangle(rr, dxBandBg);
            RenderTarget.DrawRoundedRectangle(rr, dxBorder, 0.8f);

            string modeTag = modoA
                ? ("MODO A · FEED NATIVO (" + nativeSymbol + ")")
                : (isOn ? ("MODO B · PROXY WEB (~" + AtualizarSegundos + "s)") : "MODO B · AGUARDANDO API");

            string tickSign = (curTick >= 0) ? ("+" + curTick.ToString("0", CultureInfo.InvariantCulture)) : curTick.ToString("0", CultureInfo.InvariantCulture);
            string topTxt = "NYSE $TICK: " + tickSign + "   [" + modeTag + "]";
            SharpDX.Direct2D1.SolidColorBrush valBrush = (curTick >= 200) ? dxBullBrush : ((curTick <= -200) ? dxBearBrush : dxTextLight);
            RenderTarget.DrawText(topTxt, dxFontTitle, new SharpDX.RectangleF(panelLeft + 16f, hudTop + 2f, hudW - 16f, 16f), modoA ? dxModoABrush : valBrush);

            if (MostrarCorrelacaoAtivo)
            {
                bool useNqCorr = (chartRoot == "NQ" || chartRoot == "MNQ" || chartRoot == "QQQ");
                StringBuilder sb = new StringBuilder();
                sb.Append("TICKQ: ").Append(tq.ToString("+0;-0;0", CultureInfo.InvariantCulture));
                sb.Append(" | ADD: ").Append(addV.ToString("+0;-0;0", CultureInfo.InvariantCulture));
                sb.Append(" | VIX: ").Append(vixV.ToString("0.00", CultureInfo.InvariantCulture)).Append(" (").Append(vixC.ToString("+0.0;-0.0;0.0", CultureInfo.InvariantCulture)).Append("%)");

                sb.Append(" | CORR [").Append(chartRoot).Append("]:");
                int added = 0;
                for (int i = 0; i < corrSnap.Count && added < 3; i++)
                {
                    MacroCorrItem item = corrSnap[i];
                    if (item.Id == chartRoot || item.Id == "ES" || item.Id == "NQ") continue;
                    double c = useNqCorr ? item.CorrNq : item.CorrEs;
                    sb.Append(" ").Append(item.Id).Append(" ").Append(c.ToString("+0.00;-0.00;0.00", CultureInfo.InvariantCulture));
                    added++;
                }
                RenderTarget.DrawText(sb.ToString(), dxFontSmall, new SharpDX.RectangleF(panelLeft + 16f, hudTop + 19f, hudW - 16f, 15f), dxTextMuted);
            }
        }

        private void LimparRecursosRender()
        {
            if (dxZoneBull != null) { dxZoneBull.Dispose(); dxZoneBull = null; }
            if (dxZoneBear != null) { dxZoneBear.Dispose(); dxZoneBear = null; }
            if (dxBandBg != null) { dxBandBg.Dispose(); dxBandBg = null; }
            if (dxBorder != null) { dxBorder.Dispose(); dxBorder = null; }
            if (dxTextLight != null) { dxTextLight.Dispose(); dxTextLight = null; }
            if (dxTextMuted != null) { dxTextMuted.Dispose(); dxTextMuted = null; }
            if (dxBullBrush != null) { dxBullBrush.Dispose(); dxBullBrush = null; }
            if (dxBearBrush != null) { dxBearBrush.Dispose(); dxBearBrush = null; }
            if (dxModoABrush != null) { dxModoABrush.Dispose(); dxModoABrush = null; }
            if (dxModoBBrush != null) { dxModoBBrush.Dispose(); dxModoBBrush = null; }
            if (dxFontTitle != null) { dxFontTitle.Dispose(); dxFontTitle = null; }
            if (dxFontSmall != null) { dxFontSmall.Dispose(); dxFontSmall = null; }
            if (dxDwFactory != null) { dxDwFactory.Dispose(); dxDwFactory = null; }
        }

        public override void OnRenderTargetChanged()
        {
            LimparRecursosRender();
        }
    }
}
'''

# ==============================================================================
# 13. ORDERFLOW IMBALANCE FLASH (ESTILO BOOKMAP MARKET PULSE + SONS NAO-VOCAIS)
# ==============================================================================
CODE_ORDERFLOW_IMBALANCE_FLASH = r'''using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Media;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.NinjaScript;
using SharpDX;
using SharpDX.Direct2D1;
using SharpDX.DirectWrite;

namespace NinjaTrader.NinjaScript.Indicators
{
    public class OrderFlowImbalanceFlash : Indicator
    {
        private struct TradeSample
        {
            public DateTime Time;
            public double Price;
            public long Volume;
            public bool IsBuy;
        }

        private class LevelFlow
        {
            public long BuyVol;
            public long SellVol;
        }

        private class FlashPriceZone
        {
            public double Price;
            public bool IsBuyDominant;
            public long NetVol;
            public long PeakVol;
            public long LastTouchMs;
        }

        private class TopPriceItem
        {
            public double Price;
            public long Delta;
        }

        private static class PcmToneSynthesizer
        {
            public static MemoryStream BuildChimeStream(double startHz, double endHz, double harmHz, int durationMs, double ampScale)
            {
                int sampleRate = 22050;
                int numSamples = Math.Max(400, (sampleRate * durationMs) / 1000);
                int dataBytes = numSamples * 2;
                byte[] wav = new byte[44 + dataBytes];

                // RIFF header
                wav[0] = (byte)'R'; wav[1] = (byte)'I'; wav[2] = (byte)'F'; wav[3] = (byte)'F';
                WriteInt32(wav, 4, 36 + dataBytes);
                wav[8] = (byte)'W'; wav[9] = (byte)'A'; wav[10] = (byte)'V'; wav[11] = (byte)'E';
                // fmt chunk
                wav[12] = (byte)'f'; wav[13] = (byte)'m'; wav[14] = (byte)'t'; wav[15] = (byte)' ';
                WriteInt32(wav, 16, 16);
                WriteInt16(wav, 20, 1); // PCM
                WriteInt16(wav, 22, 1); // Mono
                WriteInt32(wav, 24, sampleRate);
                WriteInt32(wav, 28, sampleRate * 2);
                WriteInt16(wav, 32, 2);
                WriteInt16(wav, 34, 16);
                // data chunk
                wav[36] = (byte)'d'; wav[37] = (byte)'a'; wav[38] = (byte)'t'; wav[39] = (byte)'a';
                WriteInt32(wav, 40, dataBytes);

                double phase = 0.0;
                double phase2 = 0.0;
                double amp = Math.Max(0.05, Math.Min(0.95, ampScale));

                for (int i = 0; i < numSamples; i++)
                {
                    double t = (double)i / (numSamples - 1);
                    double envIn = (i < 220) ? (0.5 - 0.5 * Math.Cos(Math.PI * i / 220.0)) : 1.0;
                    double envOut = Math.Pow(1.0 - t, 1.35);
                    double freq = startHz + (endHz - startHz) * t;
                    phase += 2.0 * Math.PI * freq / sampleRate;
                    phase2 += 2.0 * Math.PI * harmHz / sampleRate;

                    double sig = 0.72 * Math.Sin(phase) + (harmHz > 0 ? 0.28 * Math.Sin(phase2) : 0.0);
                    double sVal = sig * envIn * envOut * amp * 26000.0;
                    short pcm = (short)Math.Max(-32760, Math.Min(32760, (int)Math.Round(sVal)));
                    WriteInt16(wav, 44 + i * 2, pcm);
                }
                return new MemoryStream(wav, false);
            }

            private static void WriteInt32(byte[] buf, int offset, int value)
            {
                buf[offset] = (byte)(value & 0xFF);
                buf[offset + 1] = (byte)((value >> 8) & 0xFF);
                buf[offset + 2] = (byte)((value >> 16) & 0xFF);
                buf[offset + 3] = (byte)((value >> 24) & 0xFF);
            }

            private static void WriteInt16(byte[] buf, int offset, short value)
            {
                buf[offset] = (byte)(value & 0xFF);
                buf[offset + 1] = (byte)((value >> 8) & 0xFF);
            }
        }

        private readonly object flowLock = new object();
        private readonly Queue<TradeSample> windowQueue = new Queue<TradeSample>();
        private readonly Dictionary<double, LevelFlow> windowLevels = new Dictionary<double, LevelFlow>();
        private readonly Dictionary<double, FlashPriceZone> flashZones = new Dictionary<double, FlashPriceZone>();

        private long winBuyVol = 0;
        private long winSellVol = 0;
        private int winBuyTrades = 0;
        private int winSellTrades = 0;
        private double lastTradePrice = 0.0;
        private bool lastTradeWasBuy = true;

        private readonly Stopwatch clockSw = Stopwatch.StartNew();
        private long lastSoundPlayMs = -99999;
        private long lastFlashImpulseMs = -99999;
        private int currentStateDir = 0; // 1 = buy imbalance, -1 = sell imbalance, 0 = neutral
        private int currentLevelIntensity = 0; // 0,1,2,3

        private SoundPlayer spBuy1, spBuy2, spBuy3;
        private SoundPlayer spSell1, spSell2, spSell3;
        private MemoryStream msBuy1, msBuy2, msBuy3;
        private MemoryStream msSell1, msSell2, msSell3;

        private bool somAtivoRuntime = true;
        private bool mouseHooked = false;
        private SharpDX.RectangleF soundBtnRect = new SharpDX.RectangleF(0, 0, 0, 0);
        private DispatcherTimer flashUiTimer;

        private SharpDX.Direct2D1.SolidColorBrush dxCardBg;
        private SharpDX.Direct2D1.SolidColorBrush dxCardBorder;
        private SharpDX.Direct2D1.SolidColorBrush dxBuyStrong;
        private SharpDX.Direct2D1.SolidColorBrush dxBuyGlow;
        private SharpDX.Direct2D1.SolidColorBrush dxSellStrong;
        private SharpDX.Direct2D1.SolidColorBrush dxSellGlow;
        private SharpDX.Direct2D1.SolidColorBrush dxNeutralBrush;
        private SharpDX.Direct2D1.SolidColorBrush dxTextLight;
        private SharpDX.Direct2D1.SolidColorBrush dxTextMuted;
        private SharpDX.Direct2D1.SolidColorBrush dxBtnBg;
        private SharpDX.DirectWrite.Factory dxDwFactory;
        private SharpDX.DirectWrite.TextFormat dxFontTitle;
        private SharpDX.DirectWrite.TextFormat dxFontBig;
        private SharpDX.DirectWrite.TextFormat dxFontSmall;

        #region Propriedades
        [NinjaScriptProperty]
        [Range(0.5, 30.0)]
        [Display(Name = "Janela Deslizante (Segundos)", Order = 1, GroupName = "01. Market Pulse Motor")]
        public double JanelaSegundos { get; set; }

        [NinjaScriptProperty]
        [Range(1, 50000)]
        [Display(Name = "Volume Minimo na Janela", Order = 2, GroupName = "01. Market Pulse Motor")]
        public int VolumeMinimoJanela { get; set; }

        [NinjaScriptProperty]
        [Range(1.1, 20.0)]
        [Display(Name = "Ratio Desequilibrio (ex: 2.2x)", Order = 3, GroupName = "01. Market Pulse Motor")]
        public double RatioDesequilibrio { get; set; }

        [NinjaScriptProperty]
        [Range(1.0, 20.0)]
        [Display(Name = "Decaimento Flash no Preco (Seg)", Order = 4, GroupName = "02. Visual e Faixas")]
        public double BrilhoDecaimentoSeg { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Mostrar Faixas Piscantes nos Niveis", Order = 5, GroupName = "02. Visual e Faixas")]
        public bool MostrarFaixasNoPreco { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Mostrar Caixinha Pulse Box", Order = 6, GroupName = "02. Visual e Faixas")]
        public bool MostrarPainelPulse { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Canto (SuperiorDireito/Esquerdo/Inferior...)", Order = 7, GroupName = "02. Visual e Faixas")]
        public string CantoPainel { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Ativar Sons Nao-Vocais Progressivos", Order = 8, GroupName = "03. Sons PCM (Zero Voz)")]
        public bool AtivarSom { get; set; }

        [NinjaScriptProperty]
        [Range(5, 100)]
        [Display(Name = "Volume Audio (%)", Order = 9, GroupName = "03. Sons PCM (Zero Voz)")]
        public int VolumeAudioPct { get; set; }

        [NinjaScriptProperty]
        [Range(150, 5000)]
        [Display(Name = "Cooldown Som Nivel 1 (ms)", Order = 10, GroupName = "03. Sons PCM (Zero Voz)")]
        public int CooldownNivel1Ms { get; set; }

        [NinjaScriptProperty]
        [Range(120, 3000)]
        [Display(Name = "Cooldown Som Nivel 2 (ms)", Order = 11, GroupName = "03. Sons PCM (Zero Voz)")]
        public int CooldownNivel2Ms { get; set; }

        [NinjaScriptProperty]
        [Range(80, 2000)]
        [Display(Name = "Cooldown Som Nivel 3 Climax (ms)", Order = 12, GroupName = "03. Sons PCM (Zero Voz)")]
        public int CooldownNivel3Ms { get; set; }
        #endregion

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Caixinha piscante estilo Bookmap Market Pulse (0ms OnMarketData), faixas de desequilibrio no preco e sons nao-vocais progressivos.";
                Name = "VeltrixQuant - OrderFlowImbalanceFlash";
                Calculate = Calculate.OnEachTick;
                IsOverlay = true;
                IsAutoScale = false;
                DisplayInDataBox = false;
                DrawOnPricePanel = true;
                PaintPriceMarkers = false;
                IsSuspendedWhileInactive = true;

                JanelaSegundos = 3.0;
                VolumeMinimoJanela = 45;
                RatioDesequilibrio = 2.2;
                BrilhoDecaimentoSeg = 4.5;
                MostrarFaixasNoPreco = true;
                MostrarPainelPulse = true;
                CantoPainel = "SuperiorDireito";
                AtivarSom = true;
                VolumeAudioPct = 65;
                CooldownNivel1Ms = 700;
                CooldownNivel2Ms = 360;
                CooldownNivel3Ms = 210;
            }
            else if (State == State.DataLoaded)
            {
                somAtivoRuntime = AtivarSom;
                InitAudioPlayers();
                HookMouseAndTimer();
            }
            else if (State == State.Terminated)
            {
                UnhookMouseAndTimer();
                DisposeAudioPlayers();
                LimparRecursosRender();
            }
        }

        private void InitAudioPlayers()
        {
            DisposeAudioPlayers();
            try
            {
                double amp = VolumeAudioPct / 100.0;
                msBuy1 = PcmToneSynthesizer.BuildChimeStream(784.0, 880.0, 1568.0, 95, amp * 0.72);
                msBuy2 = PcmToneSynthesizer.BuildChimeStream(988.0, 1244.0, 1975.0, 105, amp * 0.85);
                msBuy3 = PcmToneSynthesizer.BuildChimeStream(1175.0, 1568.0, 2349.0, 120, amp * 1.00);

                msSell1 = PcmToneSynthesizer.BuildChimeStream(349.0, 311.0, 0.0, 95, amp * 0.74);
                msSell2 = PcmToneSynthesizer.BuildChimeStream(294.0, 220.0, 147.0, 110, amp * 0.88);
                msSell3 = PcmToneSynthesizer.BuildChimeStream(220.0, 146.8, 110.0, 125, amp * 1.00);

                spBuy1 = new SoundPlayer(msBuy1); spBuy1.Load();
                spBuy2 = new SoundPlayer(msBuy2); spBuy2.Load();
                spBuy3 = new SoundPlayer(msBuy3); spBuy3.Load();
                spSell1 = new SoundPlayer(msSell1); spSell1.Load();
                spSell2 = new SoundPlayer(msSell2); spSell2.Load();
                spSell3 = new SoundPlayer(msSell3); spSell3.Load();
            }
            catch { }
        }

        private void DisposeAudioPlayers()
        {
            SoundPlayer[] pls = new SoundPlayer[] { spBuy1, spBuy2, spBuy3, spSell1, spSell2, spSell3 };
            for (int i = 0; i < pls.Length; i++)
            {
                if (pls[i] != null) { try { pls[i].Stop(); pls[i].Dispose(); } catch { } }
            }
            spBuy1 = spBuy2 = spBuy3 = spSell1 = spSell2 = spSell3 = null;

            MemoryStream[] mss = new MemoryStream[] { msBuy1, msBuy2, msBuy3, msSell1, msSell2, msSell3 };
            for (int i = 0; i < mss.Length; i++)
            {
                if (mss[i] != null) { try { mss[i].Dispose(); } catch { } }
            }
            msBuy1 = msBuy2 = msBuy3 = msSell1 = msSell2 = msSell3 = null;
        }

        private void HookMouseAndTimer()
        {
            if (ChartControl == null) return;
            ChartControl.Dispatcher.InvokeAsync(new Action(() =>
            {
                if (State == State.Terminated || ChartControl == null) return;
                if (!mouseHooked)
                {
                    ChartControl.MouseDown += OnChartMouseDown;
                    mouseHooked = true;
                }
                if (flashUiTimer == null)
                {
                    flashUiTimer = new DispatcherTimer(DispatcherPriority.Render, ChartControl.Dispatcher);
                    flashUiTimer.Interval = TimeSpan.FromMilliseconds(150);
                    flashUiTimer.Tick += (s, ev) =>
                    {
                        if (ChartControl == null || State != State.Realtime) return;
                        long nowMs = clockSw.ElapsedMilliseconds;
                        if (nowMs - lastFlashImpulseMs <= (long)(BrilhoDecaimentoSeg * 1000.0) + 400)
                            ChartControl.InvalidateVisual();
                    };
                    flashUiTimer.Start();
                }
            }));
        }

        private void UnhookMouseAndTimer()
        {
            if (ChartControl == null) return;
            try
            {
                ChartControl.Dispatcher.InvokeAsync(new Action(() =>
                {
                    if (ChartControl != null && mouseHooked)
                    {
                        ChartControl.MouseDown -= OnChartMouseDown;
                        mouseHooked = false;
                    }
                    if (flashUiTimer != null)
                    {
                        flashUiTimer.Stop();
                        flashUiTimer = null;
                    }
                }));
            }
            catch { }
        }

        private void OnChartMouseDown(object sender, MouseButtonEventArgs e)
        {
            if (ChartControl == null || ChartControl.PresentationSource == null || !MostrarPainelPulse) return;
            System.Windows.Point p = e.GetPosition(ChartControl);
            float px = (float)ChartingExtensions.ConvertToHorizontalPixels(p.X, ChartControl.PresentationSource);
            float py = (float)ChartingExtensions.ConvertToVerticalPixels(p.Y, ChartControl.PresentationSource);

            if (soundBtnRect.Width > 0 && soundBtnRect.Contains(px, py))
            {
                somAtivoRuntime = !somAtivoRuntime;
                e.Handled = true;
                ChartControl.InvalidateVisual();
            }
        }

        protected override void OnBarUpdate()
        {
        }

        protected override void OnMarketData(MarketDataEventArgs e)
        {
            if (BarsInProgress != 0 || e == null || e.MarketDataType != MarketDataType.Last || e.Volume <= 0 || e.Price <= 0)
                return;

            double ask = (e.Ask > 0) ? e.Ask : GetCurrentAsk();
            double bid = (e.Bid > 0) ? e.Bid : GetCurrentBid();
            bool isBuy;

            if (ask > 0 && e.Price >= ask) isBuy = true;
            else if (bid > 0 && e.Price <= bid) isBuy = false;
            else if (lastTradePrice > 0)
            {
                if (e.Price > lastTradePrice) isBuy = true;
                else if (e.Price < lastTradePrice) isBuy = false;
                else isBuy = lastTradeWasBuy;
            }
            else isBuy = true;

            lastTradePrice = e.Price;
            lastTradeWasBuy = isBuy;

            DateTime nowRef = (e.Time != DateTime.MinValue) ? e.Time : DateTime.Now;
            long nowMonoMs = clockSw.ElapsedMilliseconds;

            int trigDir = 0;
            int trigLevel = 0;

            lock (flowLock)
            {
                windowQueue.Enqueue(new TradeSample { Time = nowRef, Price = e.Price, Volume = e.Volume, IsBuy = isBuy });
                if (isBuy) { winBuyVol += e.Volume; winBuyTrades++; }
                else { winSellVol += e.Volume; winSellTrades++; }

                LevelFlow lf;
                if (!windowLevels.TryGetValue(e.Price, out lf))
                {
                    lf = new LevelFlow();
                    windowLevels[e.Price] = lf;
                }
                if (isBuy) lf.BuyVol += e.Volume;
                else lf.SellVol += e.Volume;

                DateTime cutoff = nowRef.AddSeconds(-JanelaSegundos);
                while (windowQueue.Count > 0 && windowQueue.Peek().Time < cutoff)
                {
                    TradeSample old = windowQueue.Dequeue();
                    if (old.IsBuy) { winBuyVol -= old.Volume; winBuyTrades--; }
                    else { winSellVol -= old.Volume; winSellTrades--; }

                    LevelFlow oldLf;
                    if (windowLevels.TryGetValue(old.Price, out oldLf))
                    {
                        if (old.IsBuy) oldLf.BuyVol = Math.Max(0, oldLf.BuyVol - old.Volume);
                        else oldLf.SellVol = Math.Max(0, oldLf.SellVol - old.Volume);
                        if (oldLf.BuyVol == 0 && oldLf.SellVol == 0) windowLevels.Remove(old.Price);
                    }
                }
                if (winBuyVol < 0) winBuyVol = 0;
                if (winSellVol < 0) winSellVol = 0;

                // Atualiza zonas piscantes por nivel de preco
                long lvlNet = lf.BuyVol - lf.SellVol;
                long minLevelBurst = Math.Max(6, VolumeMinimoJanela / 3);
                if (Math.Abs(lvlNet) >= minLevelBurst)
                {
                    FlashPriceZone zone;
                    if (!flashZones.TryGetValue(e.Price, out zone))
                    {
                        zone = new FlashPriceZone { Price = e.Price };
                        flashZones[e.Price] = zone;
                    }
                    zone.IsBuyDominant = (lvlNet >= 0);
                    zone.NetVol = Math.Abs(lvlNet);
                    if (zone.NetVol > zone.PeakVol) zone.PeakVol = zone.NetVol;
                    zone.LastTouchMs = nowMonoMs;
                    lastFlashImpulseMs = nowMonoMs;
                }

                // Avalia desequilibrio global da janela
                double buyRatio = (winSellVol > 0) ? ((double)winBuyVol / winSellVol) : (winBuyVol > 0 ? 9.9 : 1.0);
                double sellRatio = (winBuyVol > 0) ? ((double)winSellVol / winBuyVol) : (winSellVol > 0 ? 9.9 : 1.0);

                if (winBuyVol >= VolumeMinimoJanela && buyRatio >= RatioDesequilibrio)
                {
                    trigDir = 1;
                    trigLevel = (winBuyVol >= VolumeMinimoJanela * 4.5) ? 3 : ((winBuyVol >= VolumeMinimoJanela * 2.2) ? 2 : 1);
                    lastFlashImpulseMs = nowMonoMs;
                }
                else if (winSellVol >= VolumeMinimoJanela && sellRatio >= RatioDesequilibrio)
                {
                    trigDir = -1;
                    trigLevel = (winSellVol >= VolumeMinimoJanela * 4.5) ? 3 : ((winSellVol >= VolumeMinimoJanela * 2.2) ? 2 : 1);
                    lastFlashImpulseMs = nowMonoMs;
                }
                currentStateDir = trigDir;
                currentLevelIntensity = trigLevel;

                // Limpa zonas expiradas
                long decayMs = (long)(BrilhoDecaimentoSeg * 1000.0);
                if (flashZones.Count > 24)
                {
                    List<double> stale = new List<double>();
                    foreach (KeyValuePair<double, FlashPriceZone> kv in flashZones)
                    {
                        if (nowMonoMs - kv.Value.LastTouchMs > decayMs) stale.Add(kv.Key);
                    }
                    for (int i = 0; i < stale.Count; i++) flashZones.Remove(stale[i]);
                }
            }

            if (State == State.Realtime && somAtivoRuntime && trigDir != 0 && trigLevel > 0)
            {
                int cooldown = (trigLevel == 3) ? CooldownNivel3Ms : ((trigLevel == 2) ? CooldownNivel2Ms : CooldownNivel1Ms);
                if (nowMonoMs - lastSoundPlayMs >= cooldown)
                {
                    lastSoundPlayMs = nowMonoMs;
                    SoundPlayer targetSp = (trigDir > 0)
                        ? (trigLevel == 3 ? spBuy3 : (trigLevel == 2 ? spBuy2 : spBuy1))
                        : (trigLevel == 3 ? spSell3 : (trigLevel == 2 ? spSell2 : spSell1));
                    if (targetSp != null)
                    {
                        try { targetSp.Play(); } catch { }
                    }
                }
            }
        }

        private void EnsureRenderResources()
        {
            if (RenderTarget == null) return;
            if (dxDwFactory == null) dxDwFactory = new SharpDX.DirectWrite.Factory();
            if (dxFontTitle == null) dxFontTitle = new SharpDX.DirectWrite.TextFormat(dxDwFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 10.5f);
            if (dxFontBig == null) dxFontBig = new SharpDX.DirectWrite.TextFormat(dxDwFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Bold, SharpDX.DirectWrite.FontStyle.Normal, 12.5f);
            if (dxFontSmall == null) dxFontSmall = new SharpDX.DirectWrite.TextFormat(dxDwFactory, "Segoe UI", SharpDX.DirectWrite.FontWeight.Normal, SharpDX.DirectWrite.FontStyle.Normal, 9.5f);

            if (dxCardBg == null) dxCardBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.05f, 0.06f, 0.11f, 0.91f));
            if (dxCardBorder == null) dxCardBorder = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.34f, 0.42f, 0.62f, 0.72f));
            if (dxBuyStrong == null) dxBuyStrong = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.10f, 0.92f, 0.56f, 0.95f));
            if (dxBuyGlow == null) dxBuyGlow = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.10f, 0.90f, 0.54f, 0.25f));
            if (dxSellStrong == null) dxSellStrong = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.98f, 0.22f, 0.36f, 0.95f));
            if (dxSellGlow == null) dxSellGlow = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.96f, 0.20f, 0.34f, 0.25f));
            if (dxNeutralBrush == null) dxNeutralBrush = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.55f, 0.62f, 0.76f, 0.85f));
            if (dxTextLight == null) dxTextLight = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.96f, 0.97f, 1.00f, 0.98f));
            if (dxTextMuted == null) dxTextMuted = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.70f, 0.76f, 0.88f, 0.90f));
            if (dxBtnBg == null) dxBtnBg = new SharpDX.Direct2D1.SolidColorBrush(RenderTarget, new SharpDX.Color4(0.14f, 0.17f, 0.26f, 0.95f));
        }

        protected override void OnRender(ChartControl chartControl, ChartScale chartScale)
        {
            if (chartControl == null || chartScale == null || ChartBars == null || ChartPanel == null || RenderTarget == null) return;
            EnsureRenderResources();

            float panelLeft = (float)ChartPanel.X;
            float panelTop = (float)ChartPanel.Y;
            float panelRight = (float)(ChartPanel.X + ChartPanel.W);
            float panelBottom = (float)(ChartPanel.Y + ChartPanel.H);
            long nowMonoMs = clockSw.ElapsedMilliseconds;
            long decayMs = (long)(BrilhoDecaimentoSeg * 1000.0);

            long buyV, sellV;
            int buyT, sellT, dirSnap, intSnap;
            List<FlashPriceZone> zoneSnap = new List<FlashPriceZone>();
            List<TopPriceItem> topLvls = new List<TopPriceItem>();

            lock (flowLock)
            {
                buyV = winBuyVol;
                sellV = winSellVol;
                buyT = winBuyTrades;
                sellT = winSellTrades;
                dirSnap = currentStateDir;
                intSnap = currentLevelIntensity;

                foreach (KeyValuePair<double, FlashPriceZone> kv in flashZones)
                {
                    if (nowMonoMs - kv.Value.LastTouchMs <= decayMs)
                        zoneSnap.Add(kv.Value);
                }

                foreach (KeyValuePair<double, LevelFlow> kv in windowLevels)
                {
                    long delta = kv.Value.BuyVol - kv.Value.SellVol;
                    if (delta != 0) topLvls.Add(new TopPriceItem { Price = kv.Key, Delta = delta });
                }
            }

            topLvls.Sort((a, b) => Math.Abs(b.Delta).CompareTo(Math.Abs(a.Delta)));

            // Passo 1: Faixas piscantes nos niveis de preco com desequilibrio
            if (MostrarFaixasNoPreco && zoneSnap.Count > 0)
            {
                int toIdx = ChartBars.ToIndex;
                float lastX = (toIdx >= 0) ? (float)chartControl.GetXByBarIndex(ChartBars, toIdx) : (panelRight - 90f);
                float xLeftZone = Math.Max(panelLeft + 20f, lastX - 180f);
                float xRightZone = Math.Min(panelRight - 14f, lastX + 28f);

                for (int i = 0; i < zoneSnap.Count; i++)
                {
                    FlashPriceZone z = zoneSnap[i];
                    float y = (float)chartScale.GetYByValue(z.Price);
                    if (y < panelTop + 6f || y > panelBottom - 6f) continue;

                    double ageFrac = Math.Max(0.0, 1.0 - ((double)(nowMonoMs - z.LastTouchMs) / Math.Max(500.0, decayMs)));
                    float blink = (float)(0.55 + 0.45 * Math.Sin(nowMonoMs * 0.014 + i));
                    float alphaFactor = (float)ageFrac * blink;

                    SharpDX.Direct2D1.SolidColorBrush glow = z.IsBuyDominant ? dxBuyGlow : dxSellGlow;
                    SharpDX.Direct2D1.SolidColorBrush line = z.IsBuyDominant ? dxBuyStrong : dxSellStrong;

                    glow.Opacity = Math.Max(0.05f, 0.42f * alphaFactor);
                    RenderTarget.FillRectangle(new SharpDX.RectangleF(xLeftZone, y - 5.5f, Math.Max(20f, xRightZone - xLeftZone), 11f), glow);
                    line.Opacity = Math.Max(0.15f, 0.95f * alphaFactor);
                    RenderTarget.DrawLine(new SharpDX.Vector2(xLeftZone, y), new SharpDX.Vector2(xRightZone, y), line, 1.4f);

                    string lbl = (z.IsBuyDominant ? "+" : "-") + z.NetVol.ToString(CultureInfo.InvariantCulture);
                    RenderTarget.DrawText(lbl, dxFontSmall, new SharpDX.RectangleF(xRightZone + 4f, y - 7f, 52f, 14f), line);
                }
                dxBuyStrong.Opacity = 0.95f;
                dxSellStrong.Opacity = 0.95f;
                dxBuyGlow.Opacity = 0.25f;
                dxSellGlow.Opacity = 0.25f;
            }

            // Passo 2: Caixinha Piscante Market Pulse + Botao Clicavel [SOM]
            if (!MostrarPainelPulse) return;

            float boxW = 262f;
            float boxH = 122f;
            string corner = (CantoPainel ?? "SuperiorDireito").ToLowerInvariant();
            float boxLeft = corner.Contains("esquerdo") ? (panelLeft + 12f) : (panelRight - boxW - 14f);
            float boxTop = corner.Contains("inferior") ? (panelBottom - boxH - 14f) : (panelTop + 12f);

            float pulseFlash = (dirSnap != 0)
                ? (float)(0.55 + 0.45 * Math.Sin(nowMonoMs * (intSnap >= 3 ? 0.022 : 0.012)))
                : 0.20f;

            SharpDX.Direct2D1.SolidColorBrush stateBrush = (dirSnap > 0) ? dxBuyStrong : ((dirSnap < 0) ? dxSellStrong : dxNeutralBrush);
            SharpDX.RectangleF cardRect = new SharpDX.RectangleF(boxLeft, boxTop, boxW, boxH);
            SharpDX.Direct2D1.RoundedRectangle rrCard = new SharpDX.Direct2D1.RoundedRectangle { Rect = cardRect, RadiusX = 6f, RadiusY = 6f };
            RenderTarget.FillRoundedRectangle(rrCard, dxCardBg);

            if (dirSnap != 0)
            {
                SharpDX.Direct2D1.SolidColorBrush flashGlow = (dirSnap > 0) ? dxBuyGlow : dxSellGlow;
                flashGlow.Opacity = 0.45f * pulseFlash;
                RenderTarget.FillRoundedRectangle(rrCard, flashGlow);
                flashGlow.Opacity = 0.25f;
            }

            stateBrush.Opacity = (dirSnap != 0) ? (0.55f + 0.45f * pulseFlash) : 0.65f;
            RenderTarget.DrawRoundedRectangle(rrCard, stateBrush, (dirSnap != 0) ? 1.8f : 0.9f);
            stateBrush.Opacity = 0.95f;

            string instName = (Instrument != null && Instrument.MasterInstrument != null) ? Instrument.MasterInstrument.Name : "ATIVO";
            RenderTarget.DrawText("MARKET PULSE · " + instName, dxFontTitle, new SharpDX.RectangleF(boxLeft + 10f, boxTop + 7f, 165f, 16f), dxTextLight);

            soundBtnRect = new SharpDX.RectangleF(boxLeft + boxW - 76f, boxTop + 6f, 66f, 17f);
            SharpDX.Direct2D1.RoundedRectangle rrBtn = new SharpDX.Direct2D1.RoundedRectangle { Rect = soundBtnRect, RadiusX = 3.5f, RadiusY = 3.5f };
            RenderTarget.FillRoundedRectangle(rrBtn, dxBtnBg);
            RenderTarget.DrawRoundedRectangle(rrBtn, somAtivoRuntime ? dxBuyStrong : dxSellStrong, 0.9f);
            RenderTarget.DrawText(somAtivoRuntime ? "SOM: ON" : "SOM: MUTE", dxFontSmall, new SharpDX.RectangleF(soundBtnRect.Left + 7f, soundBtnRect.Top + 1.5f, 56f, 14f), somAtivoRuntime ? dxBuyStrong : dxTextMuted);

            long totalV = buyV + sellV;
            double ratioShow = (dirSnap > 0)
                ? ((sellV > 0) ? (double)buyV / sellV : buyV)
                : ((dirSnap < 0) ? ((buyV > 0) ? (double)sellV / buyV : sellV) : 1.0);

            string headStatus = (dirSnap > 0)
                ? ("IMPULSO COMPRA (" + ratioShow.ToString("0.1", CultureInfo.InvariantCulture) + "x · L" + intSnap + ")")
                : ((dirSnap < 0)
                    ? ("PRESSAO VENDA (" + ratioShow.ToString("0.1", CultureInfo.InvariantCulture) + "x · L" + intSnap + ")")
                    : "EQUILIBRIO DE FLUXO");

            RenderTarget.DrawText(headStatus, dxFontBig, new SharpDX.RectangleF(boxLeft + 10f, boxTop + 26f, boxW - 20f, 18f), stateBrush);

            // Barra dividida % Compra vs % Venda
            float barX = boxLeft + 10f;
            float barY = boxTop + 48f;
            float barW = boxW - 20f;
            float buyFrac = (totalV > 0) ? ((float)buyV / totalV) : 0.5f;
            RenderTarget.FillRectangle(new SharpDX.RectangleF(barX, barY, barW, 8f), dxSellStrong);
            RenderTarget.FillRectangle(new SharpDX.RectangleF(barX, barY, barW * buyFrac, 8f), dxBuyStrong);

            double speedTradesSec = (JanelaSegundos > 0) ? ((buyT + sellT) / JanelaSegundos) : 0.0;
            long netDelta = buyV - sellV;
            string statsLine = "C: " + buyV + "  |  V: " + sellV + "  |  Δ: " + netDelta.ToString("+0;-0;0", CultureInfo.InvariantCulture) + "  |  " + speedTradesSec.ToString("0.0", CultureInfo.InvariantCulture) + " tr/s";
            RenderTarget.DrawText(statsLine, dxFontSmall, new SharpDX.RectangleF(boxLeft + 10f, boxTop + 60f, boxW - 20f, 14f), dxTextLight);

            string top1 = (topLvls.Count > 0) ? ("Top1 @ " + topLvls[0].Price.ToString("0.##", CultureInfo.InvariantCulture) + " (" + topLvls[0].Delta.ToString("+0;-0;0", CultureInfo.InvariantCulture) + ")") : "Aguardando lotes no Tape...";
            string top2 = (topLvls.Count > 1) ? ("Top2 @ " + topLvls[1].Price.ToString("0.##", CultureInfo.InvariantCulture) + " (" + topLvls[1].Delta.ToString("+0;-0;0", CultureInfo.InvariantCulture) + ")") : ("Janela " + JanelaSegundos.ToString("0.0", CultureInfo.InvariantCulture) + "s · Min " + VolumeMinimoJanela);
            RenderTarget.DrawText(top1, dxFontSmall, new SharpDX.RectangleF(boxLeft + 10f, boxTop + 80f, boxW - 20f, 14f), dxTextMuted);
            RenderTarget.DrawText(top2, dxFontSmall, new SharpDX.RectangleF(boxLeft + 10f, boxTop + 96f, boxW - 20f, 14f), dxTextMuted);
        }

        private void LimparRecursosRender()
        {
            if (dxCardBg != null) { dxCardBg.Dispose(); dxCardBg = null; }
            if (dxCardBorder != null) { dxCardBorder.Dispose(); dxCardBorder = null; }
            if (dxBuyStrong != null) { dxBuyStrong.Dispose(); dxBuyStrong = null; }
            if (dxBuyGlow != null) { dxBuyGlow.Dispose(); dxBuyGlow = null; }
            if (dxSellStrong != null) { dxSellStrong.Dispose(); dxSellStrong = null; }
            if (dxSellGlow != null) { dxSellGlow.Dispose(); dxSellGlow = null; }
            if (dxNeutralBrush != null) { dxNeutralBrush.Dispose(); dxNeutralBrush = null; }
            if (dxTextLight != null) { dxTextLight.Dispose(); dxTextLight = null; }
            if (dxTextMuted != null) { dxTextMuted.Dispose(); dxTextMuted = null; }
            if (dxBtnBg != null) { dxBtnBg.Dispose(); dxBtnBg = null; }
            if (dxFontTitle != null) { dxFontTitle.Dispose(); dxFontTitle = null; }
            if (dxFontBig != null) { dxFontBig.Dispose(); dxFontBig = null; }
            if (dxFontSmall != null) { dxFontSmall.Dispose(); dxFontSmall = null; }
            if (dxDwFactory != null) { dxDwFactory.Dispose(); dxDwFactory = null; }
        }

        public override void OnRenderTargetChanged()
        {
            LimparRecursosRender();
        }
    }
}
'''

# ==============================================================================
# ESCREVENDO E ORGANIZANDO TUDO NA PASTA DA MARCA (VeltrixQuant)
# ==============================================================================
pasta_marca = os.path.join(pasta_destino, MARCA_PASTA)
os.makedirs(pasta_marca, exist_ok=True)

arquivos_para_instalar = {
    "NiveisEstruturaPro.cs": CODE_ESTRUTURA,
    "NiveisGammaPro.cs": CODE_GAMMA,
    "MoneyRiskPro.cs": CODE_RISK_V76,
    "DailyOHLCPro.cs": CODE_OHLC,
    "GlobexRangePro.cs": CODE_GLOBEX,
    "VolatilidadeImplicitaPro.cs": CODE_VOLATILIDADE,
    "FluentliExpectedMove.cs": CODE_EXPECTED_MOVE,
    "VWAPInstitucionalPro.cs": CODE_VWAP,
    "DeltaCumulativePro.cs": CODE_DELTA,
    "FluentliWatchdog.cs": CODE_WATCHDOG,
    "DarkPoolBeamsPro.cs": CODE_DARKPOOL_BEAMS,
    "NyseTickBreadthPro.cs": CODE_NYSE_TICK_BREADTH,
    "OrderFlowImbalanceFlash.cs": CODE_ORDERFLOW_IMBALANCE_FLASH,
}

PREFIXOS_ECOSISTEMA = (
    "Fluentli",
    "Veltrix",
    "GexProfile",
    "NiveisEstrutura",
    "NiveisGamma",
    "MoneyRisk",
    "DailyOHLC",
    "GlobexRange",
    "VolatilidadeImplicita",
    "VWAPInstitucional",
    "DeltaCumulative",
    "DarkPoolBeams",
    "NyseTickBreadth",
    "OrderFlowImbalance",
)

print(f"\n--- ORGANIZANDO PASTA DA MARCA: {pasta_marca} ---")
try:
    realocados = []
    duplicatas_raiz_removidas = []

    for item in os.listdir(pasta_destino):
        origem_raiz = os.path.join(pasta_destino, item)
        if not os.path.isfile(origem_raiz):
            continue
        if item.startswith("@") or not item.lower().endswith(".cs"):
            continue

        if item in arquivos_para_instalar:
            try:
                os.remove(origem_raiz)
                duplicatas_raiz_removidas.append(item)
                print(f"🧹 DUPLICATA NA RAIZ REMOVIDA (sera instalada em {MARCA_PASTA}): {item}")
            except Exception as exc_rm:
                print(f"⚠️ Nao foi possivel remover {item} da raiz: {exc_rm}")
        elif item.startswith(PREFIXOS_ECOSISTEMA):
            destino_marca = os.path.join(pasta_marca, item)
            if not os.path.exists(destino_marca):
                try:
                    shutil.move(origem_raiz, destino_marca)
                    realocados.append(item)
                    print(f"📦 REALOCADO PARA {MARCA_PASTA}: {item}")
                except Exception as exc_mv:
                    print(f"⚠️ Nao foi possivel mover {item}: {exc_mv}")

    for nome_arquivo, conteudo in arquivos_para_instalar.items():
        caminho_completo = os.path.join(pasta_marca, nome_arquivo)
        if os.path.exists(caminho_completo):
            try:
                os.remove(caminho_completo)
            except Exception:
                pass
        with open(caminho_completo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        print(f"✅ SUCESSO: {MARCA_PASTA}/{nome_arquivo} instalado/atualizado.")

    caminho_url_cfg = os.path.join(pasta_marca, "VeltrixQuant_URL.txt")
    url_atual_cfg = ""
    if os.path.exists(caminho_url_cfg):
        try:
            with open(caminho_url_cfg, "r", encoding="utf-8") as f_old:
                url_atual_cfg = f_old.read().strip()
        except Exception:
            url_atual_cfg = ""
    if (not url_atual_cfg) or (url_atual_cfg == "http://localhost:3000"):
        with open(caminho_url_cfg, "w", encoding="utf-8") as f:
            f.write(DASHBOARD_URL_PADRAO + "\n")
        print(f"🌐 URL NUVEM CONFIGURADA EM: {caminho_url_cfg} -> {DASHBOARD_URL_PADRAO}")

    resumo_movidos = f"\n🧹 Duplicatas removidas da raiz: {len(duplicatas_raiz_removidas)} | Extras movidos: {len(realocados)}"
    messagebox.showinfo(
        f"Instalação MESTRE {MARCA_PASTA} Concluída",
        "✅ SUCESSO TOTAL!\n\n"
        f"📂 Pasta criada/organizada:\n{pasta_marca}\n"
        f"{resumo_movidos}\n\n"
        f"Foram instalados {len(arquivos_para_instalar)} Indicadores ({MARCA_PASTA} - ...):\n"
        "1. NiveisEstruturaPro (Gamma Histograma)\n"
        "2. NiveisGammaPro (Linhas e Dashboard)\n"
        "3. MoneyRiskPro (Versão V76 - ATR Inteligente)\n"
        "4. DailyOHLCPro (Faixa Vertical RTH)\n"
        "5. GlobexRangePro (Apenas Linhas)\n"
        "6. VolatilidadeImplicitaPro (Bandas 1, 2 e 3 SD da IV)\n"
        "7. FluentliExpectedMove (Nuvens de Expected Move)\n"
        "8. VWAPInstitucionalPro (VWAP + 4 Desvios SD)\n"
        "9. DeltaCumulativePro (Fluxo de Agressão v2.0)\n"
        "10. FluentliWatchdog (Icebergs Dinâmicos/Sintéticos & Rastreio)\n"
        "11. DarkPoolBeamsPro (Feixes Lilás SEC/FINRA + Barra de Força)\n"
        "12. NyseTickBreadthPro (Modo A Automático + Proxy Web + Correlação)\n"
        "13. OrderFlowImbalanceFlash (Market Pulse Bookmap + Sons Não-Vocais)\n\n"
        "👉 AGORA: Abra o NinjaTrader, abra o NinjaScript Editor e aperte F5 (Compile).",
    )

except Exception as e:
    messagebox.showerror("Erro Fatal", f"Não foi possível gravar os arquivos:\n{e}")