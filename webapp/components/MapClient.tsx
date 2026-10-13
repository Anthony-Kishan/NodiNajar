"use client";
import dynamic from "next/dynamic";
export const RiverMap = dynamic(() => import("./RiverMap"), { ssr: false, loading: () => <div className="skeleton" style={{ position: "absolute", inset: 0, height: "auto" }} /> });
export const CompareMap = dynamic(() => import("./CompareMap"), { ssr: false });
