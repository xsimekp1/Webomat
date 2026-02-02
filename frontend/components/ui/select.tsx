export default function Select({ children, ...props }: { children: React.ReactNode; [key: string]: any }) {
  return <select {...props}>{children}</select>
}