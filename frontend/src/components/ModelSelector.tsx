'use client'

const MODELS = [
  { id: 'gemini',  label: 'Gemini 2.0 Flash',  color: 'from-blue-500 to-cyan-500' },
  { id: 'gpt',     label: 'GPT-4o',             color: 'from-green-500 to-emerald-500' },
  { id: 'claude',  label: 'Claude 3.5 Sonnet',  color: 'from-orange-500 to-amber-500' },
  { id: 'mock',    label: 'Mock (offline)',      color: 'from-zinc-500 to-zinc-400' },
]

interface Props {
  value: string
  onChange: (val: string) => void
}

export default function ModelSelector({ value, onChange }: Props) {
  return (
    <div>
      <label className="text-xs text-zinc-400 mb-2 block uppercase tracking-wider">AI Model</label>
      <div className="grid grid-cols-2 gap-2">
        {MODELS.map((m) => (
          <button
            key={m.id}
            onClick={() => onChange(m.id)}
            className={`px-3 py-2 rounded-lg text-xs font-semibold border transition-all text-left
              ${value === m.id
                ? `bg-gradient-to-r ${m.color} text-white border-transparent`
                : 'bg-[#0f0f1a] border-[#3a3a5c] text-zinc-400 hover:border-violet-500/50 hover:text-white'
              }`}
          >
            {m.label}
          </button>
        ))}
      </div>
    </div>
  )
}
