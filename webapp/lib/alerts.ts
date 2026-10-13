import { bnDigits } from "./format";
import type { SegmentProps } from "./types";

/** Fixed templates filled from measured numbers. No AI writes alerts (project rule). Same wording as web/app.js. */
export function alertText(p: SegmentProps, days: number, lang: "bn" | "en"): string {
  const m = Math.round(p.retreat_m);
  if (lang === "bn") {
    return `নদীনজর সতর্কবার্তা: গত ${bnDigits(days)} দিনে আপনার এলাকায় যমুনার পাড় ${bnDigits(m)} মিটার সরে এসেছে। ভাঙনের ঝুঁকি: ${p.level === "red" ? "উচ্চ" : "মাঝারি"}। মূল্যবান জিনিস ও গবাদিপশু নিরাপদ স্থানে সরানোর প্রস্তুতি নিন এবং ইউনিয়ন পরিষদের সাথে যোগাযোগ করুন। (${p.id})`;
  }
  return `NodiNajar alert: in the last ${days} days the Jamuna bank near you moved ${m} m. Erosion risk: ${p.level === "red" ? "HIGH" : "MEDIUM"}. Prepare to move valuables and livestock to safety and contact your union parishad. (${p.id})`;
}

export function audience(level: SegmentProps["level"]): string[] {
  return level === "red"
    ? ["Families within 200 m (SMS + voice call)", "Union parishad", "Upazila office", "Water Development Board"]
    : ["Officials and NGOs (dashboard and email)"];
}
