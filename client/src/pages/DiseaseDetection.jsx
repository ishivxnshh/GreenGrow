// client/src/pages/DiseaseDetection.jsx
import { useState } from "react";
import { GiPlantWatering } from "react-icons/gi";
import { AiOutlineCheckCircle, AiOutlineExclamationCircle } from "react-icons/ai";
import { MdOutlineScience } from "react-icons/md";
import jsPDF from "jspdf";

function DiseaseDetection() {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const diseaseInfo = {
    "Tomato - Early Blight": {
      description: "Early blight is a common fungal disease that causes leaf spots and reduces yield.",
      remedies: ["Remove and destroy infected leaves.", "Rotate crops to prevent spread.", "Use fungicide sprays (consult experts)."]
    },
    "Healthy Plant": { description: "No visible signs of disease detected.", remedies: ["Maintain proper watering schedule.", "Regularly check for pests."] }
  };

  const handleImageChange = (e) => {
    setImage(e.target.files[0]);
    setResult("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      const fakeResult = "Detected: Tomato - Early Blight 🌿";
      setResult(fakeResult);
      setHistory((prev) => [{ img: URL.createObjectURL(image), res: fakeResult }, ...prev]);
      setLoading(false);
    }, 2000);
  };

  return (
    <div className="relative w-screen min-h-screen">
      <div className="absolute inset-0 w-full h-full bg-cover bg-center -z-10" style={{ backgroundImage: "url('https://images.unsplash.com/photo-1593529467227-35f093d1c148?auto=format&fit=crop&w=1350&q=80')" }}>
        <div className="absolute inset-0 bg-white/50 backdrop-blur-sm"></div>
      </div>

      <div className="relative max-w-4xl mx-auto p-8">
        <h2 className="text-4xl font-extrabold text-green-800 mb-3 text-center flex items-center justify-center gap-3">
          <GiPlantWatering size={35} /> Disease Detection
        </h2>

        <p className="text-center text-gray-700 mb-8 text-lg">
          Upload a clear picture of your crop leaf 🍃 and we'll analyze it for possible diseases and give remedies.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6 bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow-lg border border-green-200 hover:shadow-2xl transition">
          <input type="file" accept="image/*" onChange={handleImageChange} className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-green-300" required />
          <div className="flex justify-center mt-4">
            {image ? (
              <img src={URL.createObjectURL(image)} alt="preview" className="w-52 h-52 object-cover rounded-xl shadow-md border border-green-200" />
            ) : (
              <div className="w-52 h-52 flex items-center justify-center rounded-xl bg-green-50 border border-green-200 text-gray-500 italic">🌱 Upload a leaf image</div>
            )}
          </div>
          <button type="submit" disabled={loading} className="w-full bg-green-700 text-white py-3 rounded-lg hover:bg-green-800 transition font-semibold flex items-center justify-center gap-2 disabled:opacity-60">
            {loading ? <span className="animate-spin border-2 border-white border-t-transparent rounded-full w-5 h-5"></span> : "Analyze"}
          </button>
        </form>

        {loading && <div className="mt-8 text-center text-green-700 font-medium animate-pulse">🔍 Analyzing your plant image...</div>}

        {result && !loading && (
          <div className="mt-8 bg-green-50 p-6 rounded-2xl shadow-md border border-green-200 transition">
            <h3 className="text-2xl font-bold text-green-800 flex items-center gap-2 mb-3">
              {result.includes("Early Blight") ? <AiOutlineExclamationCircle className="text-red-500" size={26} /> : <AiOutlineCheckCircle className="text-green-500" size={26} />} {result}
            </h3>
            <p className="text-gray-700 mb-4">{diseaseInfo["Tomato - Early Blight"].description}</p>
            <div className="bg-white/80 p-4 rounded-xl shadow-sm border border-green-100">
              <h4 className="text-lg font-semibold text-green-700 mb-2 flex items-center gap-2"><MdOutlineScience /> Suggested Remedies</h4>
              <ul className="list-disc list-inside text-gray-700 space-y-1">{diseaseInfo["Tomato - Early Blight"].remedies.map((tip, i) => <li key={i}>{tip}</li>)}</ul>
            </div>
          </div>
        )}

        {history.length > 0 && (
          <div className="mt-12">
            <h3 className="text-2xl font-bold text-green-800 mb-6 text-center">📜 Analysis History</h3>
            <div className="grid md:grid-cols-3 sm:grid-cols-2 grid-cols-1 gap-6">
              {history.map((item, idx) => (
                <div key={idx} className="bg-white p-4 rounded-xl shadow-md border border-green-100 hover:shadow-lg transition flex flex-col">
                  <img src={item.img} alt="history-leaf" className="w-full h-32 object-cover rounded-lg mb-3" />
                  <p className="text-green-800 font-semibold text-sm mb-2">{item.res}</p>
                  <button onClick={() => {
                      const doc = new jsPDF();
                      doc.setFontSize(16);
                      doc.text("Plant Disease Detection Report", 10, 20);
                      doc.setFontSize(12);
                      doc.text(`Result: ${item.res}`, 10, 40);
                      doc.text("Description:", 10, 55);
                      doc.text(diseaseInfo["Tomato - Early Blight"].description, 10, 65, { maxWidth: 180 });
                      doc.text("Suggested Remedies:", 10, 95);
                      diseaseInfo["Tomato - Early Blight"].remedies.forEach((tip, i) => {
                        doc.text(`- ${tip}`, 15, 110 + i * 10);
                      });
                      doc.save(`disease_report_${idx + 1}.pdf`);
                    }} className="mt-auto bg-green-700 text-white text-sm py-2 px-3 rounded-lg hover:bg-green-800 transition">📥 Download Report</button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DiseaseDetection;
