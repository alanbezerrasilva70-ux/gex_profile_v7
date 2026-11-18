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
                Name = "NiveisEstruturaPro"; Calculate = Calculate.OnEachTick; IsOverlay = true;
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
                Name = "NiveisGammaPro"; Calculate = Calculate.OnEachTick; IsOverlay = true; DisplayInDataBox = true; DrawOnPricePanel = true; ScaleJustification = NinjaTrader.Gui.Chart.ScaleJustification.Right;
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
                Name = "VolatilidadeImplicitaPro"; 
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
                Name = "FluentliExpectedMove";
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
                Name = "VWAPInstitucionalPro";
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
"""

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
    "FluentliExpectedMove.cs": CODE_EXPECTED_MOVE,
    "VWAPInstitucionalPro.cs": CODE_VWAP,
    "DeltaCumulativePro.cs": CODE_DELTA,
    "FluentliWatchdog.cs": CODE_WATCHDOG
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
                        "7. FluentliExpectedMove (Nuvens de Expected Move)\n"
                        "8. VWAPInstitucionalPro (VWAP + 4 Desvios SD)\n"
                        "9. DeltaCumulativePro (Fluxo de Agressão v2.0)\n"
                        "10. FluentliWatchdog (Icebergs Dinâmicos & Sintéticos)\n\n"
                        "👉 AGORA: Abra o NinjaTrader e aperte F5 (ou reinicie).")

except Exception as e:
    messagebox.showerror("Erro Fatal", f"Não foi possível gravar os arquivos:\n{e}")