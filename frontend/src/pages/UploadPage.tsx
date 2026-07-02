import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { listExtractions, uploadFiling } from '../api/extractions'

export function UploadPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)

  const mutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('No file selected')
      await uploadFiling(file, 'json')
      const [fresh] = await listExtractions({ sourceReference: `upload:${file.name}` })
      return fresh
    },
    onSuccess: (extraction) => {
      if (extraction) navigate(`/extractions/${extraction.id}`)
    },
  })

  return (
    <div>
      <p>
        <Link to="/">{t('filings.back')}</Link>
      </p>
      <h1>{t('upload.title')}</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          mutation.mutate()
        }}
      >
        <input
          type="file"
          accept=".xbrl,.xml,.htm,.html"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button type="submit" disabled={mutation.isPending || !file}>
          {mutation.isPending ? t('upload.uploading') : t('upload.submit')}
        </button>
      </form>

      {mutation.isError && <p className="error">{(mutation.error as Error).message}</p>}
    </div>
  )
}
