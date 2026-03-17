import Image from "next/image";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeConfig = {
  sm: { width: 24, height: 12, container: "w-6 h-3" },
  md: { width: 32, height: 16, container: "w-8 h-4" },
  lg: { width: 40, height: 20, container: "w-10 h-5" },
};

export default function Logo({ size = "md", className = "" }: LogoProps) {
  const config = sizeConfig[size];

  return (
    <div className={`flex items-center justify-center ${config.container} ${className}`}>
      <Image
        src="/images.png"
        alt="SkillPack"
        width={config.width}
        height={config.height}
        className="object-contain"
      />
    </div>
  );
}
