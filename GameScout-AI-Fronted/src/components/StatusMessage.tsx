interface Props { kind: 'error' | 'success'; message: string }

export function StatusMessage({ kind, message }: Props) {
  return <div className={`message message--${kind}`} role={kind === 'error' ? 'alert' : 'status'}>{message}</div>;
}
