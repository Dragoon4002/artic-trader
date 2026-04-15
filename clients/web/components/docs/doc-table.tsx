import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import type { ReactNode } from "react";

export function DocTable({
  headers,
  rows,
}: {
  headers: ReactNode[];
  rows: ReactNode[][];
}) {
  return (
    <div className="mb-4">
      <Table className="text-[13px] text-white/60 [&_tr]:border-white/8">
        <TableHeader className="[&_tr]:border-white/10">
          <TableRow className="border-white/5 hover:bg-white/3">
            {headers.map((h, i) => (
              <TableHead
                key={i}
                className="text-white/80 font-semibold text-[13px] h-9"
              >
                {h}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, i) => (
            <TableRow key={i} className="border-white/5 hover:bg-white/3">
              {row.map((cell, j) => (
                <TableCell key={j} className="text-[13px] py-2">
                  {cell}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
