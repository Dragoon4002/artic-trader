import type { MDXComponents } from "mdx/types";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    h1: ({ children }) => (
      <h1 className="text-3xl font-bold tracking-tight text-white mb-6 mt-10 first:mt-0">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-2xl font-semibold tracking-tight text-white mb-4 mt-10 border-b border-white/8 pb-3">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-lg font-semibold text-white mb-3 mt-8">
        {children}
      </h3>
    ),
    h4: ({ children }) => (
      <h4 className="text-base font-semibold text-white mb-2 mt-6">
        {children}
      </h4>
    ),
    p: ({ children }) => (
      <p className="text-[15px] text-white/60 leading-relaxed mb-4">
        {children}
      </p>
    ),
    a: ({ href, children }) => (
      <a
        href={href}
        className="text-orange-light hover:text-orange-text underline underline-offset-2 transition-colors"
      >
        {children}
      </a>
    ),
    ul: ({ children }) => (
      <ul className="list-disc list-inside space-y-1.5 text-[15px] text-white/60 mb-4 ml-2">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className="list-decimal list-inside space-y-1.5 text-[15px] text-white/60 mb-4 ml-2">
        {children}
      </ol>
    ),
    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
    code: ({ children, className }) => {
      // Inline code (no className means no language specified = inline)
      if (!className) {
        return (
          <code className="bg-orange/15 text-orange-text text-[13px] px-1.5 py-0.5 rounded font-mono">
            {children}
          </code>
        );
      }
      // Block code inside <pre>
      return <code className={className}>{children}</code>;
    },
    pre: ({ children }) => (
      <pre className="bg-white/3 border border-white/8 rounded-xl p-4 mb-4 overflow-x-auto text-[13px] leading-relaxed font-mono text-white/70">
        {children}
      </pre>
    ),
    table: ({ children }) => (
      <div className="mb-4">
        <Table className="text-[13px] text-white/60 [&_tr]:border-white/8">
          {children}
        </Table>
      </div>
    ),
    thead: ({ children }) => (
      <TableHeader className="[&_tr]:border-white/10">{children}</TableHeader>
    ),
    tbody: ({ children }) => <TableBody>{children}</TableBody>,
    tr: ({ children }) => (
      <TableRow className="border-white/5 hover:bg-white/3">{children}</TableRow>
    ),
    th: ({ children }) => (
      <TableHead className="text-white/80 font-semibold text-[13px] h-9">
        {children}
      </TableHead>
    ),
    td: ({ children }) => (
      <TableCell className="text-[13px] py-2">{children}</TableCell>
    ),
    blockquote: ({ children }) => (
      <blockquote className="border-l-2 border-orange-light/50 pl-4 my-4 text-white/50 italic">
        {children}
      </blockquote>
    ),
    details: ({ children, ...props }) => (
      <details
        className="my-4 rounded-lg border border-white/8 bg-white/3 overflow-hidden group/details open:border-orange-light/30"
        {...props}
      >
        {children}
      </details>
    ),
    summary: ({ children }) => (
      <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-white/80 hover:text-white select-none transition-colors">
        {children}
      </summary>
    ),
    hr: () => <hr className="border-white/8 my-8" />,
    strong: ({ children }) => (
      <strong className="text-white font-semibold">{children}</strong>
    ),
    ...components,
  };
}
