export default function Badge({ children, ...props }: { children: React.ReactNode; [key: string]: any }) {
  return <span {...props}>{children}</span>
}