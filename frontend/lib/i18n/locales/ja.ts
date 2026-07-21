import type { Dictionary } from './en'

const ja: Dictionary = {
  common: {
    search: '検索',
    cancel: 'キャンセル',
    close: '閉じる',
  },
  app: {
    name: 'FinExtract',
    tagline: 'XBRL・財務データ',
  },
  sidebar: {
    closeMenu: 'メニューを閉じる',
    openMenu: 'メニューを開く',
    extractionsBadge: '{{count}} 件の抽出',
    nav: {
      search: { label: '開示書類検索', description: '開示書類を検索・抽出' },
      extractions: { label: '抽出履歴', description: '履歴・統合・エクスポート' },
      viewer: { label: 'データビューア', description: '損益計算書・貸借対照表・キャッシュフロー' },
      charts: { label: '図表', description: 'ビジュアル分析' },
    },
  },
  languageSwitcher: {
    label: '言語',
  },
  filingSearch: {
    title: '開示書類検索',
    subtitle: 'SEC EDGAR / EDINETの開示書類を検索、またはXBRLファイルをアップロード',
    tabs: {
      'sec-edgar': 'SEC EDGAR',
      edinet: 'EDINET',
      'xbrl-api': 'XBRL API',
      'upload-xbrl': 'XBRLファイル',
      'upload-pdf': 'PDF / OCR',
    },
    notSupported: 'サーバー側で未対応です。SEC EDGARを利用するか、XBRLファイルをアップロードしてください。',
    searchPlaceholderSecEdgar: '企業名、ティッカー、またはCIK…',
    searchPlaceholderEdinet: '企業名またはティッカー…',
    searchButton: '検索',
    searchingCompanies: '企業を検索中…',
    noCompaniesFound: '企業が見つかりません。別のキーワードでお試しください。',
    enterCompanyPrompt: '企業名またはティッカーを入力して検索してください',
    dropFile: 'XBRLファイルをここにドロップ',
    acceptsFiles: '.xbrl、.xmlファイルに対応',
    fileReady: 'ファイルの準備ができました',
    backToCompanies: '企業一覧に戻る',
    loadingFilings: '開示書類を読み込み中…',
    noFilingsFound: 'この企業の開示書類は見つかりませんでした。',
    loadMore: 'さらに読み込む',
    filed: '{{date}} 提出',
    idLabel: {
      'sec-edgar': 'CIK',
      edinet: 'EDINETコード',
    },
    extractPanel: {
      selectFilingPrompt: '抽出する開示書類を選択してください',
      selectFilingHint: '開示ソースを検索するか、ファイルをアップロードして選択してください',
      backToResults: '検索結果に戻る',
      filedLabel: '{{idLabel}}：{{identifier}} · 提出日：{{date}}',
      extractionNameLabel: '抽出名',
      extractionNamePlaceholder: '例：Apple 10-Q 2025年第3四半期',
      extractionNameHint: '抽出履歴に生のドキュメントURLの代わりに表示されます。',
      bodyText:
        '標準化されたすべての項目（損益計算書、貸借対照表、キャッシュフロー計算書）が抽出されます。データ取得後に表示行を絞り込めます。',
      launchExtraction: '抽出を開始',
      extracting: '抽出中…',
    },
    toasts: {
      extractionCompleted: '抽出が完了しました：{{count}} 会計年度',
      viewAction: '表示',
      extractionFailed: '抽出に失敗しました',
      nothingSelected: '抽出対象が選択されていません',
    },
  },
  extractions: {
    title: '抽出履歴',
    countSummary:
      '{{filings}} 件の開示書類（{{periods}} 期間）· 選択して統合・エクスポート・表示できます',
    selected: '{{count}} 件選択中',
    mergeAndView: '統合して表示',
    exportXlsx: 'XLSXをエクスポート',
    filterPlaceholder: '抽出履歴を絞り込み…',
    columns: {
      company: '企業',
      period: '期間',
      standard: '基準',
      extracted: '抽出日時',
      actions: '操作',
    },
    selectAll: 'すべて選択',
    noExtractions: '抽出履歴はまだありません',
    noExtractionsHint: '開示書類検索から抽出を実行すると、ここに表示されます',
    periodsBadge: '{{count}} 期間',
    viewData: 'データを表示',
    view: '表示',
    xlsx: 'XLSX',
    toasts: {
      pleaseSelect: 'エクスポートする抽出を選択してください。',
      exportReady: 'XLSXエクスポートの準備ができました',
      exportFailed: 'エクスポートに失敗しました',
      selectAtLeastTwo: '統合するには2件以上選択してください。',
    },
  },
  charts: {
    title: '図表',
    settings: '設定',
    chartSettingsTitle: 'グラフ設定',
    chartType: 'グラフの種類',
    bar: '棒グラフ',
    line: '折れ線グラフ',
    area: 'エリアグラフ',
    extractionsLabel: '抽出データ',
    metrics: '指標',
    selectExtractionsHint: '上で抽出データを選択すると、利用可能な指標が表示されます',
    tapSettingsToSelect: '設定をタップして抽出データを選択してください',
    selectMetricPrompt: '設定で少なくとも1つの指標を選択してください',
    selectExtractionsToVisualize: '可視化する抽出データを選択してください',
    metricsComparison: '{{count}} 指標の比較',
  },
  landing: {
    nav: {
      signIn: 'ログイン',
    },
    hero: {
      badge: 'XBRL · SEC EDGAR · EDINET',
      title: '公式開示書類から財務諸表を、手作業なしで',
      subtitle:
        'FinExtract は SEC EDGAR(米国)と EDINET(日本)から XBRL データを直接取得し、比較可能な損益計算書・貸借対照表・キャッシュフロー計算書に正規化して、Excel や CSV にエクスポートします。',
      cta: 'Google でログイン',
      ctaHint: '無料 — Google アカウントが必要です',
    },
    features: {
      title: '主な機能',
      sources: {
        title: '公式データソース',
        description:
          'SEC EDGAR と EDINET から企業を検索し、開示書類(10-K、10-Q、有価証券報告書)を直接閲覧できます。',
      },
      extraction: {
        title: 'ワンクリック抽出',
        description:
          '書類を選ぶだけで、FinExtract が XBRL を解析。損益計算書・貸借対照表・キャッシュフローを、文書内の全会計年度分抽出します。',
      },
      normalization: {
        title: '正規化と比較',
        description:
          '勘定科目は US GAAP と日本基準をまたぐ共通タクソノミにマッピングされ、両市場の開示を並べて比較できます。',
      },
      export: {
        title: 'エクスポートと可視化',
        description:
          '複数年度を統合し、主要指標をグラフ化。整形済みの CSV / Excel ファイルとして出力できます。',
      },
    },
    about: {
      title: 'このプロジェクトについて',
      body: 'FinExtract は、Damien MATHIEU が東北大学 工学部(仙台)での研究インターンシップ中に開発しました。',
      goal: '目標は、米国と日本の規制当局の公式開示を一箇所で抽出・正規化し、市場をまたいだ財務諸表分析を身近にすることです。',
    },
    footer: {
      credit: '© {{year}} Damien MATHIEU — 東北大学 工学部',
      sources: 'データ: SEC EDGAR · EDINET',
    },
  },
  dataViewer: {
    title: 'データビューア',
    noExtractionsSelected: '抽出データが選択されていません',
    extractionsMerged: '{{count}} 件の抽出データを統合',
    charts: 'グラフ',
    xlsx: 'XLSX',
    selectExtractionsToView: '表示する抽出データを選択してください',
    extractionsSelectedCount: '{{count}} 件の抽出データを選択中',
    noExtractionsYet: '抽出履歴はまだありません',
    noDataForSheet: '選択された抽出データにはこのシートのデータがありません。',
    field: '項目',
    xbrlTag: 'XBRLタグ',
    sheets: {
      is: { label: '損益計算書', short: 'PL' },
      bs: { label: '貸借対照表', short: 'BS' },
      cf: { label: 'キャッシュフロー', short: 'CF' },
    },
    useSelectorHint: '上のセレクターを使用するか、抽出履歴ページから移動してください',
    toasts: {
      exportSuccess: 'XLSXのエクスポートに成功しました',
      exportFailed: 'エクスポートに失敗しました',
    },
  },
}

export default ja
