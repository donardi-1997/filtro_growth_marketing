"""Static profile configuration and parsing constants."""

APP_TITLE = "Ranking de Candidatos - Marketing"

PROFILE = {
    "cargo": "Growth & Marketing Lead",
    "experiencia_objetivo_min": 6,
    "experiencia_objetivo_ideal": 8,
    "criterios": {
        "estrategia_growth": {
            "peso": 18,
            "keywords": [
                "growth marketing", "growth", "estrategia de marketing",
                "marketing estrategico", "planeacion estrategica", "go to market",
                "go-to-market", "posicionamiento", "generacion de demanda",
                "demand generation", "expansion de mercado", "market expansion",
                "desarrollo de negocio", "business development",
            ],
        },
        "conexion_comercial": {
            "peso": 15,
            "keywords": [
                "ventas", "comercial", "equipo comercial", "sales", "pipeline",
                "funnel", "embudo", "lead", "leads", "conversion", "cierre",
                "clientes b2b", "b2b", "b2c", "revenue", "facturacion",
            ],
        },
        "presupuesto": {
            "peso": 12,
            "keywords": [
                "presupuesto", "budget", "ad spend", "inversion",
                "manejo de presupuesto", "gestion presupuestal", "paid media budget",
            ],
            "strong_patterns": [
                r"\b(?:administre|administro|gestione|gestiono|maneje|manejo|lidere|lidero|responsable de)\b.{0,45}\b(?:presupuesto|budget|inversion|ad spend)\b",
                r"\b(?:presupuesto|budget|inversion|ad spend)\b.{0,45}\b(?:de|por|superior a|hasta)?\s*(?:cop|usd|\$)\s*[\d\.,]+",
                r"\b(?:cop|usd|\$)\s*[\d\.,]+\s*(?:millones|mm|m)?\b.{0,45}\b(?:presupuesto|budget|inversion|ad spend|paid media)\b",
            ],
        },
        "metricas_resultados": {
            "peso": 15,
            "keywords": [
                "roi", "roas", "cac", "ltv", "cpl", "cpa", "ctr", "kpi", "kpis",
                "tasa de conversion", "conversion rate", "ventas generadas",
                "crecimiento de ingresos", "performance", "rentabilidad", "retorno",
            ],
        },
        "campanas_activaciones_eventos": {
            "peso": 12,
            "keywords": [
                "campanas 360", "campana 360", "atl", "btl", "activaciones",
                "activacion de marca", "eventos", "lanzamientos", "ferias",
                "networking", "relaciones publicas", "public relations", "pr",
            ],
        },
        "digital_paid_media": {
            "peso": 10,
            "keywords": [
                "meta ads", "facebook ads", "google ads", "tiktok ads",
                "linkedin ads", "paid media", "seo", "sem", "google analytics",
                "ga4", "performance marketing",
            ],
        },
        "crm_automatizacion": {
            "peso": 7,
            "keywords": [
                "hubspot", "salesforce", "crm", "automatizacion", "automation",
                "mailchimp", "manychat", "zoho", "kommo", "bitrix24",
                "marketing automation",
            ],
        },
        "liderazgo": {
            "peso": 7,
            "keywords": [
                "lidere equipo", "liderazgo", "coordine equipo", "coordinacion de equipos",
                "marketing manager", "growth manager", "director de marketing",
                "jefe de mercadeo", "lider de marketing", "agencias", "proveedores",
                "stakeholders",
            ],
        },
        "sectores_deseables": {
            "peso": 4,
            "keywords": [
                "e-commerce", "ecommerce", "retail", "logistica", "logistics",
                "startup", "marketplace", "fulfillment", "comercio electronico",
            ],
        },
    },
}

MONTHS = {
    "enero": 1, "ene": 1, "january": 1, "jan": 1,
    "febrero": 2, "feb": 2, "february": 2,
    "marzo": 3, "mar": 3, "march": 3,
    "abril": 4, "abr": 4, "april": 4, "apr": 4,
    "mayo": 5, "may": 5,
    "junio": 6, "jun": 6, "june": 6,
    "julio": 7, "jul": 7, "july": 7,
    "agosto": 8, "ago": 8, "august": 8, "aug": 8,
    "septiembre": 9, "sep": 9, "sept": 9, "september": 9,
    "octubre": 10, "oct": 10, "october": 10,
    "noviembre": 11, "nov": 11, "november": 11,
    "diciembre": 12, "dic": 12, "december": 12, "dec": 12,
}

WORK_HEADINGS = {
    "experiencia", "experiencia laboral", "experiencia profesional",
    "trayectoria profesional", "historial laboral", "work experience",
    "professional experience", "employment history", "career experience",
}
EDUCATION_HEADINGS = {
    "educacion", "formacion", "formacion academica", "educacion academica",
    "estudios", "academic background", "education", "certificaciones",
    "certifications", "cursos", "courses",
}
OTHER_SECTION_HEADINGS = {
    "perfil", "perfil profesional", "resumen", "resumen profesional", "habilidades",
    "skills", "competencias", "idiomas", "languages", "referencias", "references",
    "proyectos", "projects", "contacto", "contact",
}
