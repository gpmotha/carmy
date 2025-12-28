import { colors } from '../../config/colors'

export default function EmptySlot({
  isDragOver = false,
  onDrop,
}) {
  return (
    <div
      className={`h-16 flex flex-col items-center justify-center rounded-xl transition-all duration-200
        ${isDragOver ? 'scale-105' : ''}`}
      style={{
        background: isDragOver ? `${colors.lavender}10` : colors.cream,
        border: isDragOver
          ? `2px dashed ${colors.lavender}`
          : `2px dashed ${colors.lavenderLight}`,
      }}
    >
      <span
        className={`text-2xl transition-opacity ${isDragOver ? 'opacity-60' : 'opacity-20'}`}
      >
        +
      </span>
      <span
        className={`text-[10px] transition-opacity ${isDragOver ? 'opacity-60' : 'opacity-30'}`}
        style={{ color: colors.stone }}
      >
        {isDragOver ? 'Release to add' : 'Drop here'}
      </span>
    </div>
  )
}
