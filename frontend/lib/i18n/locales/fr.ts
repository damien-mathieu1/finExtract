import type { Dictionary } from './en'

const fr: Dictionary = {
  common: {
    search: 'Rechercher',
    cancel: 'Annuler',
    close: 'Fermer',
  },
  app: {
    name: 'FinExtract',
    tagline: 'XBRL · Données financières',
  },
  sidebar: {
    closeMenu: 'Fermer le menu',
    openMenu: 'Ouvrir le menu',
    extractionsBadge: '{{count}} extractions',
    nav: {
      search: { label: 'Recherche de dépôts', description: 'Rechercher et extraire des dépôts' },
      extractions: { label: 'Extractions', description: 'Historique, fusion & export' },
      viewer: { label: 'Visualiseur', description: 'Tableaux CR / Bilan / Flux' },
      charts: { label: 'Graphiques', description: 'Analyse visuelle' },
    },
  },
  languageSwitcher: {
    label: 'Langue',
  },
  filingSearch: {
    title: 'Recherche de dépôts',
    subtitle: 'Rechercher des dépôts SEC EDGAR / EDINET ou importer votre propre fichier XBRL',
    tabs: {
      'sec-edgar': 'SEC EDGAR',
      edinet: 'EDINET',
      'xbrl-api': 'API XBRL',
      'upload-xbrl': 'Fichier XBRL',
      'upload-pdf': 'PDF / OCR',
    },
    notSupported:
      "Pas encore pris en charge par le serveur. Essayez SEC EDGAR ou importez un fichier XBRL.",
    searchPlaceholderSecEdgar: 'Société, symbole ou CIK…',
    searchPlaceholderEdinet: 'Nom de société ou symbole…',
    searchButton: 'Rechercher',
    searchingCompanies: 'Recherche de sociétés…',
    noCompaniesFound: 'Aucune société trouvée. Essayez une autre recherche.',
    enterCompanyPrompt: 'Saisissez un nom de société ou un symbole pour rechercher',
    dropFile: 'Déposez le fichier XBRL ici',
    acceptsFiles: 'Fichiers .xbrl, .xml acceptés',
    fileReady: 'Fichier prêt pour extraction',
    backToCompanies: 'Retour aux sociétés',
    loadingFilings: 'Chargement des dépôts…',
    noFilingsFound: 'Aucun dépôt trouvé pour cette société.',
    loadMore: 'Charger plus',
    filed: 'Déposé le {{date}}',
    idLabel: {
      'sec-edgar': 'CIK',
      edinet: 'Code EDINET',
    },
    extractPanel: {
      selectFilingPrompt: 'Sélectionnez un dépôt à extraire',
      selectFilingHint:
        'Recherchez une source de dépôts ou importez un fichier, puis sélectionnez-en un pour continuer',
      backToResults: 'Retour aux résultats',
      filedLabel: '{{idLabel}} : {{identifier}} · Déposé le : {{date}}',
      extractionNameLabel: "Nom de l'extraction",
      extractionNamePlaceholder: 'ex. Apple 10-Q T3 2025',
      extractionNameHint: "Affiché dans l'historique des extractions à la place de l'URL brute.",
      bodyText:
        'Tous les champs standardisés (compte de résultat, bilan, flux de trésorerie) seront extraits. Vous pourrez filtrer les lignes à afficher une fois les données disponibles.',
      launchExtraction: "Lancer l'extraction",
      extracting: 'Extraction en cours…',
    },
    toasts: {
      extractionCompleted: 'Extraction terminée : {{count}} exercice(s)',
      viewAction: 'Voir',
      extractionFailed: "Échec de l'extraction",
      nothingSelected: 'Rien à extraire',
    },
  },
  extractions: {
    title: 'Extractions',
    countSummary:
      '{{filings}} dépôt{{filingsPlural}} ({{periods}} période{{periodsPlural}}) · Sélectionnez pour fusionner, exporter ou afficher',
    selected: '{{count}} sélectionné(s)',
    mergeAndView: 'Fusionner & afficher',
    exportXlsx: 'Exporter XLSX',
    filterPlaceholder: 'Filtrer les extractions…',
    columns: {
      company: 'Société',
      period: 'Période',
      standard: 'Norme',
      extracted: 'Extrait le',
      actions: 'Actions',
    },
    selectAll: 'Tout sélectionner',
    noExtractions: 'Aucune extraction pour le moment',
    noExtractionsHint: 'Lancez une extraction depuis Recherche de dépôts pour la voir ici',
    periodsBadge: '{{count}} périodes',
    viewData: 'Voir les données',
    view: 'Voir',
    xlsx: 'XLSX',
    toasts: {
      pleaseSelect: 'Veuillez sélectionner des extractions à exporter.',
      exportReady: 'Export XLSX prêt',
      exportFailed: "Échec de l'export",
      selectAtLeastTwo: 'Sélectionnez au moins 2 extractions à fusionner.',
    },
  },
  charts: {
    title: 'Graphiques',
    settings: 'Paramètres',
    chartSettingsTitle: 'Paramètres du graphique',
    chartType: 'Type de graphique',
    bar: 'Barres',
    line: 'Ligne',
    area: 'Zone',
    extractionsLabel: 'Extractions',
    metrics: 'Indicateurs',
    selectExtractionsHint: 'Sélectionnez des extractions ci-dessus pour voir les indicateurs disponibles',
    tapSettingsToSelect: 'Appuyez sur Paramètres pour sélectionner des extractions',
    selectMetricPrompt: 'Sélectionnez au moins un indicateur dans Paramètres',
    selectExtractionsToVisualize: 'Sélectionnez des extractions à visualiser',
    metricsComparison: 'Comparaison de {{count}} indicateurs',
  },
  landing: {
    nav: {
      signIn: 'Se connecter',
    },
    hero: {
      badge: 'XBRL · SEC EDGAR · EDINET',
      title: 'Les états financiers des dépôts officiels, sans travail manuel',
      subtitle:
        "FinExtract extrait les données XBRL directement depuis SEC EDGAR (États-Unis) et EDINET (Japon), les normalise en comptes de résultat, bilans et flux de trésorerie comparables, et exporte le tout vers Excel ou CSV.",
      cta: 'Se connecter avec Google',
      ctaHint: 'Gratuit — compte Google requis',
    },
    features: {
      title: 'Fonctionnalités',
      sources: {
        title: 'Sources officielles',
        description:
          'Recherchez des sociétés et parcourez leurs dépôts directement depuis SEC EDGAR et EDINET — 10-K, 10-Q, rapports annuels sur titres.',
      },
      extraction: {
        title: 'Extraction en un clic',
        description:
          "Choisissez un dépôt et FinExtract analyse le XBRL sous-jacent : compte de résultat, bilan et flux de trésorerie, pour chaque exercice présent dans le document.",
      },
      normalization: {
        title: 'Normalisé & comparable',
        description:
          'Les postes sont rattachés à une taxonomie commune entre US GAAP et GAAP japonais, pour comparer côte à côte les dépôts des deux marchés.',
      },
      export: {
        title: 'Export & visualisation',
        description:
          'Fusionnez plusieurs exercices, tracez les indicateurs clés et exportez des fichiers CSV ou Excel propres, prêts pour vos propres modèles.',
      },
    },
    about: {
      title: 'À propos du projet',
      body: "FinExtract a été développé par Damien MATHIEU dans le cadre d'un stage de recherche à la School of Engineering de l'Université du Tohoku (Sendai, Japon).",
      goal: "Son objectif : rendre accessible l'analyse comparée des états financiers entre marchés, en extrayant et normalisant les dépôts officiels des régulateurs américain et japonais au même endroit.",
    },
    footer: {
      credit: '© {{year}} Damien MATHIEU — School of Engineering, Université du Tohoku',
      sources: 'Données : SEC EDGAR · EDINET',
    },
  },
  dataViewer: {
    title: 'Visualiseur de données',
    noExtractionsSelected: 'Aucune extraction sélectionnée',
    extractionsMerged: '{{count}} extractions fusionnées',
    charts: 'Graphiques',
    xlsx: 'XLSX',
    selectExtractionsToView: 'Sélectionnez des extractions à afficher',
    extractionsSelectedCount: '{{count}} extraction(s) sélectionnée(s)',
    noExtractionsYet: 'Aucune extraction pour le moment',
    noDataForSheet: 'Aucune donnée pour cette feuille dans les extractions sélectionnées.',
    field: 'Champ',
    xbrlTag: 'Tag XBRL',
    sheets: {
      is: { label: 'Compte de résultat', short: 'CR' },
      bs: { label: 'Bilan', short: 'Bilan' },
      cf: { label: 'Flux de trésorerie', short: 'Flux' },
    },
    useSelectorHint: "Utilisez le sélecteur ci-dessus ou naviguez depuis la page Extractions",
    toasts: {
      exportSuccess: 'Export XLSX réussi',
      exportFailed: "Échec de l'export",
    },
  },
}

export default fr
