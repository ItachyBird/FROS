// src/components/AircraftSelector.jsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

export default function AircraftSelector({
  aircraft,
  value,
  onChange,
  disabled = false,
}) {
  const aircraftTypes = [
    { model: "Jet", display: "Jet Aircraft" },
    { model: "Piston", display: "Piston Engine Aircraft" },
    { model: "Turboprop", display: "Turboprop Aircraft" },
  ];

  return (
    <div className="space-y-2" style={{ color: "#c9c7ba" }}>
      <Label htmlFor="aircraft-select" style={{ color: "#c9c7ba" }}>
        Aircraft Type
      </Label>
      <Select
        disabled={disabled}
        value={value?.model || ""}
        onValueChange={(model) => {
          const selected = aircraftTypes.find((ac) => ac.model === model);
          onChange(selected);
        }}
      >
        <SelectTrigger
          id="aircraft-select"
          className="w-full"
          style={{
            backgroundColor: "#1f1f21",
            color: "#c9c7ba",
            borderColor: "#3c3c3c",
          }}
        >
          <SelectValue placeholder="Select Aircraft Type" />
        </SelectTrigger>
        <SelectContent
          style={{
            backgroundColor: "#1f1f21",
            color: "#c9c7ba",
            borderColor: "#3c3c3c",
          }}
        >
          {aircraftTypes.map((ac) => (
            <SelectItem
              key={ac.model}
              value={ac.model}
              style={{
                backgroundColor: "#1f1f21",
                color: "#c9c7ba",
              }}
            >
              {ac.display}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
