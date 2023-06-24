import logo from "./logo.svg";
import "./App.css";
import Background from "./idea-background.png";
import Banner from "./banner.png";
import Document from "./document.png";
import DocumentHover from "./document_hover.png";
import { useEffect, useState } from "react";
import { saveAs } from "file-saver";
import forge from "node-forge";
import LaptopPdf from "./LaptopPdf.pdf";
import FuelPdf from "./FuelPdf.pdf";
import BobaPdf from "./BobaPdf.pdf";
import SoapPdf from "./SoapPdf.pdf";

import { Button, Spinner, ThemeProvider } from "@primer/react";

const rectangles = [
  { id: 1, title: "Solar-Powered Laptop", file: LaptopPdf },
  { id: 2, title: "Microbial Fuel Cells", file: FuelPdf },
  { id: 3, title: "Rainbow Tapioca Boba", file: BobaPdf },
  { id: 4, title: "Magnetic Soap", file: SoapPdf },
];

function App() {
  const [offset, setOffset] = useState(0);

  const totalWidth = rectangles.reduce((sum, rect) => sum + rect.width + 20, 0); // width + margin-right

  const [idea, setIdea] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [fileUrl, setFileUrl] = useState("");

  function utf8encode(text) {
    return forge.util.encodeUtf8(text);
  }

  function utf8decode(text) {
    return forge.util.decodeUtf8(text);
  }

  function generatePdf() {
    setLoading(true);
    setSubmitted(true);
    fetch("https://patent-search-390320.uc.r.appspot.com/get_pdf", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        idea: idea,
        images: [],
      }),
    })
      .then((res) => res.json())
      .then((base64String) => {
        var encoded = utf8encode(base64String);
        var bytes = forge.util.decode64(encoded);
        var file = new File([bytes], "IdeaSleuth_Report.pdf", {
          type: "application/pdf",
        });
        saveAs(file);
        setLoading(false);
      })
      .catch((error) => console.error("Error:", error));
  }

  return (
    <ThemeProvider>
      <div
        className="App"
        style={{
          backgroundImage: `url(${Background})`,
          width: "100%",
          height: "102vh",
          backgroundSize: "cover",
          backgroundRepeat: "no-repeat",
          backgroundPosition: "center",
          marginTop: "-20px",
          overflowY: "hidden",
        }}
      >
        <img
          src={Banner}
          style={{
            width: "130px",
            position: "absolute",
            right: "0",
            marginRight: "70px",
            cursor: "pointer",
          }}
          onClick={() => {
            window.open("https://pinecone-hackathon.devpost.com/", "_blank");
          }}
        />
        <h1 style={{ fontSize: "28px", fontWeight: "900", marginTop: "50px" }}>
          IdeaSleuth
        </h1>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            width: "60%",
            marginLeft: "20%",
            gap: "20px",
          }}
        >
          <div
            style={{
              width: "50%",
              borderRadius: "15px",
              background: "white",
              textAlign: "initial",
              padding: "5px",
              display: "flex",
              gap: "20px",
              alignItems: "center",
              paddingLeft: "20px",
              paddingRight: "20px",
              boxShadow: "0px 0px 22px 0px rgba(111, 111, 111, 0.25)",
            }}
          >
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "50%",
                background: "#D9D9D9",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                flexShrink: 0,
                overflow: "hidden",
              }}
            >
              <h1 style={{ fontSize: "20px", fontWeight: "900" }}>1</h1>
            </div>
            <div>
              <h2 style={{ fontSize: "13px", fontWeight: "700" }}>
                Describe your Ideas and Upload Sketches
              </h2>
              <p style={{ fontSize: "11px", marginTop: "-10px" }}>
                Have an idea? Great! Describe it and IdeaSleuth will find
                patents from across the globe related to your idea, regardless
                of what language they are in.
              </p>
            </div>
          </div>
          <div
            style={{
              width: "50%",
              borderRadius: "15px",
              background: "white",
              textAlign: "initial",
              padding: "5px",
              display: "flex",
              gap: "20px",
              alignItems: "center",
              paddingLeft: "20px",
              paddingRight: "20px",
              boxShadow: "0px 0px 22px 0px rgba(111, 111, 111, 0.25)",
            }}
          >
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "50%",
                background: "#D9D9D9",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                flexShrink: 0,
                overflow: "hidden",
              }}
            >
              <h1 style={{ fontSize: "20px", fontWeight: "900" }}>2</h1>
            </div>
            <div>
              <h2 style={{ fontSize: "13px", fontWeight: "700" }}>
                Get back a Patent/IP Report and Analysis
              </h2>
              <p style={{ fontSize: "11px", marginTop: "-10px" }}>
                IdeaSleuth will take the patents it finds, read them, and
                generate a detailed analysis and report for you (including a
                score of how patentable it is).
              </p>
            </div>
          </div>
        </div>
        <div
          style={{
            width: "61%",
            marginLeft: "20%",
            display: "flex",
            gap: "50px",
            marginTop: "10px",
          }}
        >
          <div style={{ width: "95%" }}>
            <p
              style={{
                textAlign: "left",
                color: "#494949",
                fontSize: "17px",
                fontWeight: "700",
              }}
            >
              Describe your idea *
            </p>
            <textarea
              placeholder="A Solar-Powered Calculator"
              value={idea}
              onChange={(e) => {
                setIdea(e.target.value);
              }}
              style={{
                width: "100%",
                height: "100px",
                border: "1px solid #CFCFCF",
                borderRadius: "20px",
                padding: "15px",
                fontSize: "14px",
                fontFamily: "sans-serif",
                boxShadow: "-2px -1px 14px 0px rgba(82, 78, 78, 0.25) inset",
                marginTop: "-10px",
              }}
            ></textarea>
            <div
              style={{
                textAlign: "left",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                width: "103%",
              }}
            >
              <p>or get started with one of these...</p>
              <div style={{ display: "flex", gap: "10px", marginTop: "0px" }}>
                <Button
                  onClick={() => {
                    setIdea(
                      "Beehives with integrated sensors and AI to monitor bee health, activity, and environmental conditions for optimizing honey production and colony well-being."
                    );
                  }}
                >
                  Smart Beehives
                </Button>
                <Button
                  onClick={() => {
                    setIdea(
                      "Edible spoons, forks, and knives made from grains or other food materials, aimed at reducing plastic waste."
                    );
                  }}
                >
                  Edible Silverware
                </Button>
                <Button
                  onClick={() => {
                    setIdea(
                      "Drones equipped with sensors and robotic arms specifically for picking fruit from trees."
                    );
                  }}
                >
                  Fruit-picking Drones
                </Button>
              </div>
            </div>
          </div>
        </div>
        <button
          style={{
            width: "60%",
            backgroundColor: "black",
            color: "white",
            borderRadius: "15px",
            padding: "10px",
            fontSize: "15px",
            fontWeight: "700",
            marginTop: "20px",
            border: "5px solid rgba(69, 69, 69, 0.72)",
            boxShadow: "0px 0px 16px 0px rgba(106, 98, 98, 0.25)",
            cursor: "pointer",
          }}
          onClick={() => generatePdf()}
        >
          🚀 &nbsp;&nbsp;&nbsp; Generate Report &nbsp;&nbsp;&nbsp; 🚀
        </button>
        {submitted && loading && (
          <div style={{ marginTop: "50px" }}>
            <div className="book">
              <div className="left-page"></div>
              <div className="right-page"></div>
              <div className="flipping-page">
                <Spinner />
              </div>
            </div>
            <p style={{ fontWeight: "700", marginTop: "20px" }}>
              Generating your Report (takes under 2 minutes)...
            </p>
            <p style={{ marginTop: "-10px" }}>
              Will automatically download when your report is ready!
            </p>
          </div>
        )}
        {!submitted && (
          <div
            style={{ textAlign: "left", marginLeft: "20%", marginTop: "50px" }}
          >
            <h3 style={{ textAlign: "left" }}>Example Reports</h3>
            <div className="ticker">
              <div className="rectangles">
                {rectangles.map((rectangle, index) => (
                  <div
                    key={index}
                    className="rectangle"
                    style={{ width: "300px" }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        flexDirection: "column",
                        height: "100%",
                      }}
                    >
                      <h2 style={{ marginTop: "-5px", fontSize: "20px" }}>
                        {rectangle.title}
                      </h2>
                      <Button
                        style={{ marginTop: "-10px" }}
                        onClick={() => {
                          window.open(rectangle.file, "_blank");
                        }}
                      >
                        View Example PDF
                      </Button>
                    </div>
                  </div>
                ))}
                {rectangles.map((rectangle, index) => (
                  <div
                    key={index}
                    className="rectangle"
                    style={{ width: "300px" }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        flexDirection: "column",
                        height: "100%",
                      }}
                    >
                      <h2 style={{ marginTop: "-5px", fontSize: "20px" }}>
                        {rectangle.title}
                      </h2>
                      <Button
                        style={{ marginTop: "-10px" }}
                        onClick={() => {
                          window.open(rectangle.file, "_blank");
                        }}
                      >
                        View Example PDF
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        {submitted && !loading && (
          <div style={{ marginTop: "40px" }}>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              style={{ width: "50px" }}
            >
              <path
                fillRule="evenodd"
                d="M8.603 3.799A4.49 4.49 0 0112 2.25c1.357 0 2.573.6 3.397 1.549a4.49 4.49 0 013.498 1.307 4.491 4.491 0 011.307 3.497A4.49 4.49 0 0121.75 12a4.49 4.49 0 01-1.549 3.397 4.491 4.491 0 01-1.307 3.497 4.491 4.491 0 01-3.497 1.307A4.49 4.49 0 0112 21.75a4.49 4.49 0 01-3.397-1.549 4.49 4.49 0 01-3.498-1.306 4.491 4.491 0 01-1.307-3.498A4.49 4.49 0 012.25 12c0-1.357.6-2.573 1.549-3.397a4.49 4.49 0 011.307-3.497 4.49 4.49 0 013.497-1.307zm7.007 6.387a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z"
                clipRule="evenodd"
              />
            </svg>

            <h2>Your Report is Ready!</h2>
            <p style={{ marginTop: "-10px" }}>
              We've downloaded your report. Open it and start building!!
            </p>
          </div>
        )}
      </div>
    </ThemeProvider>
  );
}

export default App;

