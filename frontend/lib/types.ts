export type FilingSource = 'sec-edgar' | 'edinet' | 'upload-xbrl'

export interface SheetRow {
  label: string
  xbrlTag: string
  [year: string]: string | number
}
