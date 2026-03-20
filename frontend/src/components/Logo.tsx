import Image from "next/image";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeConfig = {
  sm: { width: 24, height: 24, container: "w-6 h-6" },
  md: { width: 32, height: 32, container: "w-8 h-8" },
  lg: { width: 40, height: 40, container: "w-10 h-10" },
};

export default function Logo({ size = "md", className = "" }: LogoProps) {
  const config = sizeConfig[size];

  return (
    <div className={`flex items-center justify-center ${config.container} ${className}`}>
      <Image
        src="/logo.svg"
        alt="SkillPack"
        width={config.width}
        height={config.height}
        className="object-contain"
        priority
      />
    </div>
  );
}
