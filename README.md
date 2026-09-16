# Ranking de Candidatos - Marketing

Aplicación local para Windows que analiza una carpeta de hojas de vida (`.pdf` y `.docx`) contra el perfil **Growth & Marketing Lead**, genera un ranking de ajuste y exporta los resultados a Excel y CSV.

## Uso de la aplicación

1. Abre `RankingMarketing.exe`.
2. Pulsa **Seleccionar carpeta**.
3. Selecciona la carpeta que contiene las hojas de vida.
4. Pulsa **Analizar candidatos**.
5. Revisa el ranking en pantalla.
6. Usa **Abrir Excel** para abrir `ranking_candidatos_marketing.xlsx`.

Los archivos de salida se guardan en la misma carpeta donde están las hojas de vida.

## Qué evalúa

El score total es de 100 puntos:

- Experiencia / seniority: 15 puntos.
- Ajuste funcional de marketing: 70 puntos.
- Resultados cuantitativos contextualizados: 15 puntos.

Dentro del ajuste funcional se evalúan estrategia/growth, conexión comercial, presupuesto, métricas, campañas/eventos, paid media, CRM/automatización, liderazgo y experiencia en sectores afines.

La V2 usa coincidencias por palabras/frases completas, evita falsos positivos como `pr` dentro de `proyecto`, intenta excluir educación de la estimación de experiencia y da más peso a resultados contextualizados como crecimiento de ventas, reducción de CAC o ROAS acompañado de cifras.

## PDFs escaneados

La versión actual no hace OCR. Si un PDF es una imagen escaneada y no contiene texto extraíble, el candidato queda marcado como **REVISIÓN MANUAL - sin texto extraíble**.

## Crear el `.exe` en Windows

La forma más sencilla es ejecutar:

```text
build_exe_windows.bat
```

El script crea un entorno aislado, instala dependencias, ejecuta las pruebas y genera:

```text
dist\RankingMarketing.exe
```

Python solo se necesita en el computador que **compila** el ejecutable. El usuario final puede ejecutar `RankingMarketing.exe` sin instalar Python.

## Ejecutar desde código fuente

En Windows puedes usar:

```text
run_source_windows.bat
```

También puedes ejecutar por consola:

```text
python marketing_cv_ranker.py --carpeta "C:\CVs\Marketing"
```

## Compilar mediante GitHub Actions

Se incluye `.github/workflows/build-windows-exe.yml`. Si este proyecto se sube a GitHub, el workflow puede ejecutarse manualmente y deja `RankingMarketing.exe` como artifact descargable.
