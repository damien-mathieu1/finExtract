export type FilingSource = 'sec-edgar' | 'edinet' | 'xbrl-api' | 'upload-xbrl' | 'upload-pdf'

export interface SheetRow {
  label: string
  xbrlTag: string
  [year: string]: string | number
}
