import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/Nav";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Dự báo cổ phiếu VN · Transformer",
  description:
    "Dự báo giá cổ phiếu thị trường chứng khoán Việt Nam bằng mô hình Transformer — BTL Học Máy (HaUI).",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="vi"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-bg text-text">
        <Nav />
        <main className="flex-1 mx-auto w-full max-w-[1280px] px-4 sm:px-6 py-8">
          {children}
        </main>
        <footer className="border-t border-border">
          <div className="mx-auto w-full max-w-[1280px] px-4 sm:px-6 py-6 text-xs text-muted flex flex-wrap gap-x-4 gap-y-1 justify-between">
            <span>BTL Học Máy · Đại học Công nghiệp Hà Nội (HaUI)</span>
            <span>Mô hình Transformer (PyTorch) · dữ liệu FiinQuantX</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
