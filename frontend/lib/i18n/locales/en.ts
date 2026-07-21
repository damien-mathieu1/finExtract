const en = {
  common: {
    search: 'Search',
    cancel: 'Cancel',
    close: 'Close',
  },
  app: {
    name: 'FinExtract',
    tagline: 'XBRL · Financial Data',
  },
  sidebar: {
    closeMenu: 'Close menu',
    openMenu: 'Open menu',
    extractionsBadge: '{{count}} extractions',
    nav: {
      search: { label: 'Filing Search', description: 'Search & extract filings' },
      extractions: { label: 'Extractions', description: 'History, merge & export' },
      viewer: { label: 'Data Viewer', description: 'IS / BS / CF tables' },
      charts: { label: 'Figures', description: 'Visual analytics' },
    },
  },
  languageSwitcher: {
    label: 'Language',
  },
  filingSearch: {
    title: 'Filing Search',
    subtitle: 'Search SEC EDGAR / EDINET filings or upload your own XBRL file',
    tabs: {
      'sec-edgar': 'SEC EDGAR',
      edinet: 'EDINET',
      'xbrl-api': 'XBRL API',
      'upload-xbrl': 'XBRL File',
      'upload-pdf': 'PDF / OCR',
    },
    notSupported: 'Not yet supported by the backend. Try SEC EDGAR or upload an XBRL file instead.',
    searchPlaceholderSecEdgar: 'Company, ticker or CIK…',
    searchPlaceholderEdinet: 'Company name or ticker…',
    searchButton: 'Search',
    searchingCompanies: 'Searching companies…',
    noCompaniesFound: 'No companies found. Try a different query.',
    enterCompanyPrompt: 'Enter a company name or ticker to search',
    dropFile: 'Drop XBRL file here',
    acceptsFiles: 'Accepts .xbrl, .xml files',
    fileReady: 'File ready to extract',
    backToCompanies: 'Back to companies',
    loadingFilings: 'Loading filings…',
    noFilingsFound: 'No filings found for this company.',
    loadMore: 'Load more',
    filed: 'Filed {{date}}',
    idLabel: {
      'sec-edgar': 'CIK',
      edinet: 'EDINET code',
    },
    extractPanel: {
      selectFilingPrompt: 'Select a filing to extract',
      selectFilingHint: 'Search a filing source or upload a filing, then choose one to proceed',
      backToResults: 'Back to results',
      filedLabel: '{{idLabel}}: {{identifier}} · Filed: {{date}}',
      extractionNameLabel: 'Extraction name',
      extractionNamePlaceholder: 'e.g. Apple 10-Q Q3 2025',
      extractionNameHint: 'Shown in extraction history instead of the raw document URL.',
      bodyText:
        'All standardized fields (income statement, balance sheet, cash flow) will be extracted. You can filter which rows to display once the data is in.',
      launchExtraction: 'Launch Extraction',
      extracting: 'Extracting…',
    },
    toasts: {
      extractionCompleted: 'Extraction completed: {{count}} fiscal year(s)',
      viewAction: 'View',
      extractionFailed: 'Extraction failed',
      nothingSelected: 'Nothing selected to extract',
    },
  },
  extractions: {
    title: 'Extractions',
    countSummary: '{{filings}} filing{{filingsPlural}} ({{periods}} period{{periodsPlural}}) · Select to merge, export, or view',
    selected: '{{count}} selected',
    mergeAndView: 'Merge & View',
    exportXlsx: 'Export XLSX',
    filterPlaceholder: 'Filter extractions…',
    columns: {
      company: 'Company',
      period: 'Period',
      standard: 'Standard',
      extracted: 'Extracted',
      actions: 'Actions',
    },
    selectAll: 'Select all',
    noExtractions: 'No extractions yet',
    noExtractionsHint: 'Run an extraction from Filing Search to see it here',
    periodsBadge: '{{count}} periods',
    viewData: 'View data',
    view: 'View',
    xlsx: 'XLSX',
    toasts: {
      pleaseSelect: 'Please select extractions to export.',
      exportReady: 'XLSX export ready',
      exportFailed: 'Export failed',
      selectAtLeastTwo: 'Select at least 2 extractions to merge.',
    },
  },
  charts: {
    title: 'Figures',
    settings: 'Settings',
    chartSettingsTitle: 'Chart Settings',
    chartType: 'Chart Type',
    bar: 'Bar',
    line: 'Line',
    area: 'Area',
    extractionsLabel: 'Extractions',
    metrics: 'Metrics',
    selectExtractionsHint: 'Select extractions above to see available metrics',
    tapSettingsToSelect: 'Tap Settings to select extractions',
    selectMetricPrompt: 'Select at least one metric in Settings',
    selectExtractionsToVisualize: 'Select extractions to visualize',
    metricsComparison: '{{count}} Metrics Comparison',
  },
  landing: {
    nav: {
      signIn: 'Sign in',
    },
    hero: {
      badge: 'XBRL · SEC EDGAR · EDINET',
      title: 'Financial statements from official filings, without the manual work',
      subtitle:
        'FinExtract pulls XBRL data straight from SEC EDGAR (United States) and EDINET (Japan), normalizes it into comparable income statements, balance sheets and cash flows, and exports everything to Excel or CSV.',
      cta: 'Sign in with Google',
      ctaHint: 'Free — Google account required',
    },
    features: {
      title: 'What it does',
      sources: {
        title: 'Official sources',
        description:
          'Search companies and browse their filings directly from SEC EDGAR and EDINET — 10-K, 10-Q, annual securities reports.',
      },
      extraction: {
        title: 'One-click extraction',
        description:
          'Pick a filing and FinExtract parses the underlying XBRL: income statement, balance sheet and cash flow, across every fiscal year in the document.',
      },
      normalization: {
        title: 'Normalized & comparable',
        description:
          'Line items are mapped to a common taxonomy across US GAAP and Japanese GAAP, so filings from both markets line up side by side.',
      },
      export: {
        title: 'Export & visualize',
        description:
          'Merge multiple years, chart key metrics, and export clean CSV or Excel files ready for your own models.',
      },
    },
    about: {
      title: 'About this project',
      body: 'FinExtract was built by Damien MATHIEU during a research internship at the School of Engineering, Tohoku University (Sendai, Japan).',
      goal: 'Its goal is to make cross-market financial statement analysis accessible: extracting and normalizing official filings from both the American and Japanese regulators so they can be compared in one place.',
    },
    footer: {
      credit: '© {{year}} Damien MATHIEU — School of Engineering, Tohoku University',
      sources: 'Data: SEC EDGAR · EDINET',
    },
  },
  dataViewer: {
    title: 'Data Viewer',
    noExtractionsSelected: 'No extractions selected',
    extractionsMerged: '{{count}} extractions merged',
    charts: 'Charts',
    xlsx: 'XLSX',
    selectExtractionsToView: 'Select extractions to view',
    extractionsSelectedCount: '{{count}} extraction(s) selected',
    noExtractionsYet: 'No extractions yet',
    noDataForSheet: 'No data for this sheet in the selected extractions.',
    field: 'Field',
    xbrlTag: 'XBRL Tag',
    sheets: {
      is: { label: 'Income Statement', short: 'IS' },
      bs: { label: 'Balance Sheet', short: 'BS' },
      cf: { label: 'Cash Flow', short: 'CF' },
    },
    useSelectorHint: 'Use the selector above or navigate from Extractions page',
    toasts: {
      exportSuccess: 'XLSX exported successfully',
      exportFailed: 'Export failed',
    },
  },
}

export default en

type DeepStringify<T> = { [K in keyof T]: T[K] extends object ? DeepStringify<T[K]> : string }
export type Dictionary = DeepStringify<typeof en>
