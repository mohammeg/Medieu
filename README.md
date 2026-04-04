<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Students Directory</title>
  <style>
    /* =========================
       Base / Reset
    ========================= */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    :root {
      --bg: #f4f7fb;
      --surface: #ffffff;
      --surface-soft: #f8fafc;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --border: #e5e7eb;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      --shadow-hover: 0 18px 40px rgba(37, 99, 235, 0.14);
      --radius-lg: 20px;
      --radius-md: 14px;
      --radius-sm: 10px;
      --container: 1200px;
    }

    body {
      font-family: Arial, Helvetica, sans-serif;
      background: linear-gradient(180deg, #eef4ff 0%, var(--bg) 100%);
      color: var(--text);
      line-height: 1.6;
    }

    img {
      display: block;
      width: 100%;
      object-fit: cover;
    }

    a {
      color: inherit;
      text-decoration: none;
    }

    button,
    input {
      font: inherit;
    }

    .directory-wrapper {
      width: 100%;
      max-width: var(--container);
      margin: 0 auto;
      padding: 32px 18px 48px;
    }

    /* =========================
       Shared UI
    ========================= */
    .section-panel {
      background: rgba(255, 255, 255, 0.88);
      border: 1px solid rgba(229, 231, 235, 0.8);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
      overflow: hidden;
    }

    .section-header {
      padding: 28px 24px 10px;
    }

    .section-title {
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: 0.2px;
      margin-bottom: 8px;
      color: #111827;
    }

    .section-subtitle {
      color: var(--muted);
      font-size: 0.98rem;
      max-width: 720px;
    }

    .hidden {
      display: none !important;
    }

    .fade-in-up {
      animation: fadeInUp 0.45s ease;
    }

    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(18px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    /* =========================
       Gallery View
    ========================= */
    .gallery-view {
      padding-bottom: 28px;
    }

    .toolbar {
      padding: 14px 24px 24px;
    }

    .search-wrap {
      position: relative;
      max-width: 560px;
    }

    .search-input {
      width: 100%;
      border: 1px solid var(--border);
      background: #fff;
      color: var(--text);
      border-radius: 999px;
      padding: 15px 18px 15px 48px;
      outline: none;
      box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
      transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
    }

    .search-input:focus {
      border-color: rgba(37, 99, 235, 0.45);
      box-shadow: 0 10px 24px rgba(37, 99, 235, 0.14);
      transform: translateY(-1px);
    }

    .search-icon {
      position: absolute;
      top: 50%;
      left: 18px;
      transform: translateY(-50%);
      color: var(--muted);
      font-size: 1rem;
      pointer-events: none;
    }

    .students-grid {
      padding: 0 24px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 22px;
    }

    .student-card {
      background: var(--surface);
      border: 1px solid rgba(229, 231, 235, 0.9);
      border-radius: var(--radius-lg);
      overflow: hidden;
      cursor: pointer;
      box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
      transition: transform 0.28s ease, box-shadow 0.28s ease, border-color 0.28s ease;
      position: relative;
    }

    .student-card:hover {
      transform: translateY(-8px);
      box-shadow: var(--shadow-hover);
      border-color: rgba(37, 99, 235, 0.22);
    }

    .student-card::after {
      content: "";
      position: absolute;
      inset: auto 0 0 0;
      height: 3px;
      background: linear-gradient(90deg, var(--primary), #60a5fa);
      transform: scaleX(0);
      transform-origin: left;
      transition: transform 0.28s ease;
    }

    .student-card:hover::after {
      transform: scaleX(1);
    }

    .student-card-image {
      width: 100%;
      aspect-ratio: 4 / 4.2;
      background: #dbeafe;
    }

    .student-card-body {
      padding: 16px 14px 18px;
      text-align: center;
    }

    .student-name {
      font-size: 1rem;
      font-weight: 700;
      color: #111827;
      line-height: 1.4;
    }

    .no-results {
      margin: 22px 24px 0;
      background: #fff;
      border: 1px dashed #cbd5e1;
      color: var(--muted);
      border-radius: 18px;
      padding: 28px 20px;
      text-align: center;
      font-size: 1rem;
    }

    /* =========================
       Details View
    ========================= */
    .details-view {
      padding-bottom: 28px;
    }

    .details-topbar {
      padding: 24px 24px 0;
    }

    .back-button {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: none;
      background: var(--primary);
      color: #fff;
      padding: 12px 18px;
      border-radius: 999px;
      cursor: pointer;
      font-weight: 700;
      box-shadow: 0 10px 18px rgba(37, 99, 235, 0.2);
      transition: background 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease;
    }

    .back-button:hover {
      background: var(--primary-dark);
      transform: translateY(-2px);
      box-shadow: 0 14px 24px rgba(29, 78, 216, 0.24);
    }

    .student-profile {
      padding: 24px;
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      gap: 26px;
      align-items: start;
    }

    .profile-sidebar,
    .profile-main {
      background: var(--surface);
      border: 1px solid rgba(229, 231, 235, 0.9);
      border-radius: 24px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }

    .profile-sidebar {
      overflow: hidden;
      position: sticky;
      top: 16px;
    }

    .profile-main {
      padding: 24px;
    }

    .profile-main-photo {
      width: 100%;
      aspect-ratio: 4 / 4.5;
      background: #dbeafe;
    }

    .profile-sidebar-content {
      padding: 20px;
    }

    .profile-name {
      font-size: 1.7rem;
      font-weight: 700;
      line-height: 1.25;
      margin-bottom: 6px;
      color: #111827;
    }

    .profile-subtext {
      color: var(--muted);
      font-size: 0.98rem;
      margin-bottom: 16px;
    }

    .profile-contact-list {
      display: grid;
      gap: 12px;
    }

    .contact-item {
      background: var(--surface-soft);
      border: 1px solid #edf2f7;
      border-radius: 14px;
      padding: 12px 14px;
    }

    .contact-label {
      display: block;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      color: var(--muted);
      margin-bottom: 4px;
      font-weight: 700;
    }

    .contact-value {
      color: var(--text);
      font-size: 0.96rem;
      word-break: break-word;
    }

    .profile-sections {
      display: grid;
      gap: 20px;
    }

    .profile-card {
      background: var(--surface-soft);
      border: 1px solid #edf2f7;
      border-radius: 20px;
      padding: 20px;
    }

    .profile-card h3 {
      font-size: 1.1rem;
      margin-bottom: 12px;
      color: #111827;
    }

    .profile-card p {
      color: #374151;
      font-size: 0.98rem;
    }

    .info-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .info-box {
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      padding: 14px 15px;
    }

    .info-label {
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      margin-bottom: 5px;
    }

    .info-value {
      color: #111827;
      font-weight: 600;
      font-size: 0.98rem;
    }

    .tag-list {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .tag-item {
      display: inline-flex;
      align-items: center;
      padding: 9px 14px;
      background: #eff6ff;
      color: #1d4ed8;
      border: 1px solid #bfdbfe;
      border-radius: 999px;
      font-size: 0.92rem;
      font-weight: 700;
    }

    .extra-gallery {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }

    .extra-gallery-item {
      width: 100%;
      aspect-ratio: 1 / 1;
      border-radius: 16px;
      overflow: hidden;
      background: #dbeafe;
      border: 1px solid #e5e7eb;
      box-shadow: 0 6px 16px rgba(15, 23, 42, 0.05);
    }

    /* =========================
       Responsive Design
    ========================= */
    @media (max-width: 1100px) {
      .students-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .student-profile {
        grid-template-columns: 300px minmax(0, 1fr);
      }
    }

    @media (max-width: 860px) {
      .section-title {
        font-size: 1.7rem;
      }

      .students-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .student-profile {
        grid-template-columns: 1fr;
      }

      .profile-sidebar {
        position: static;
      }

      .extra-gallery {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 560px) {
      .directory-wrapper {
        padding: 18px 12px 28px;
      }

      .section-header,
      .toolbar,
      .details-topbar {
        padding-left: 16px;
        padding-right: 16px;
      }

      .students-grid {
        grid-template-columns: 1fr;
        padding: 0 16px;
      }

      .student-profile {
        padding: 16px;
      }

      .profile-main {
        padding: 18px;
      }

      .info-grid {
        grid-template-columns: 1fr;
      }

      .extra-gallery {
        grid-template-columns: 1fr 1fr;
      }

      .profile-name {
        font-size: 1.45rem;
      }

      .search-input {
        padding-left: 44px;
      }
    }
  </style>
</head>
<body>
  <div class="directory-wrapper">
    <!-- =========================
         Students Directory Section
         Easy to expand later with more sections
    ========================= -->
    <div class="section-panel" id="studentsDirectorySection">
      
      <!-- Gallery View -->
      <section id="galleryView" class="gallery-view">
        <div class="section-header">
          <h1 class="section-title">Students Directory</h1>
          <p class="section-subtitle">
            Browse student profiles, search by name, and open complete student details in the same page.
          </p>
        </div>

        <div class="toolbar">
          <div class="search-wrap">
            <span class="search-icon">&#128269;</span>
            <input
              type="text"
              id="studentSearchInput"
              class="search-input"
              placeholder="Search students by name..."
              aria-label="Search students by name"
            />
          </div>
        </div>

        <div id="studentsGrid" class="students-grid"></div>

        <div id="noResultsMessage" class="no-results hidden">
          No students found. Please try a different name.
        </div>
      </section>

      <!-- Details View -->
      <section id="detailsView" class="details-view hidden">
        <div class="details-topbar">
          <button id="backButton" class="back-button" type="button">
            &#8592; Back to Students
          </button>
        </div>

        <div id="studentDetailsContainer" class="student-profile"></div>
      </section>
    </div>
  </div>

  <script>
    /* ==========================================
       Student Data
       Replace image URLs later with your own images
    ========================================== */
    var studentsData = [
      {
        id: "STU-2026-001",
        fullName: "Emma Richardson",
        age: 16,
        grade: "11th Grade",
        department: "Science Section",
        email: "emma.richardson@example.com",
        phone: "+1 555-210-1001",
        address: "214 Maple Avenue, Springfield, IL",
        bio: "Emma is a motivated science student with a strong interest in biology, chemistry, and medical research. She enjoys participating in science fairs and school community projects.",
        subjects: ["Biology", "Chemistry", "English Literature", "Mathematics", "Research Skills"],
        photo: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=900&q=80",
        gallery: [
          "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=900&q=80"
        ]
      },
      {
        id: "STU-2026-002",
        fullName: "Liam Carter",
        age: 17,
        grade: "12th Grade",
        department: "Technology Section",
        email: "liam.carter@example.com",
        phone: "+1 555-210-1002",
        address: "88 Oak Street, Madison, WI",
        bio: "Liam is passionate about programming, robotics, and problem-solving. He often helps classmates with coding assignments and enjoys building small web applications.",
        subjects: ["Computer Science", "Physics", "Mathematics", "Robotics", "JavaScript Basics"],
        photo: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80",
        gallery: [
          "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1504593811423-6dd665756598?auto=format&fit=crop&w=900&q=80"
        ]
      },
      {
        id: "STU-2026-003",
        fullName: "Sophia Bennett",
        age: 15,
        grade: "10th Grade",
        department: "Arts Section",
        email: "sophia.bennett@example.com",
        phone: "+1 555-210-1003",
        address: "46 Cedar Lane, Austin, TX",
        bio: "Sophia is a creative student who enjoys painting, visual design, and art history. She contributes to school exhibitions and is known for her detailed sketch work.",
        subjects: ["Fine Arts", "History", "Design Basics", "Creative Writing", "Presentation Skills"],
        photo: "https://images.unsplash.com/photo-1512316609839-ce289d3eba0a?auto=format&fit=crop&w=900&q=80",
        gallery: [
          "https://images.unsplash.com/photo-1512316609839-ce289d3eba0a?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1521119989659-a83eee488004?auto=format&fit=crop&w=900&q=80"
        ]
      },
      {
        id: "STU-2026-004",
        fullName: "Noah Thompson",
        age: 16,
        grade: "11th Grade",
        department: "Commerce Section",
        email: "noah.thompson@example.com",
        phone: "+1 555-210-1004",
        address: "119 Birch Road, Denver, CO",
        bio: "Noah is interested in business studies, accounting, and teamwork. He enjoys organizing student events and learning how real-world businesses operate.",
        subjects: ["Economics", "Business Studies", "Accounting", "Communication", "Leadership"],
        photo: "https://images.unsplash.com/photo-1504257432389-52343af06ae3?auto=format&fit=crop&w=900&q=80",
        gallery: [
          "https://images.unsplash.com/photo-1504257432389-52343af06ae3?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1504593811423-6dd665756598?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1496345965480-90d19731e543?auto=format&fit=crop&w=900&q=80"
        ]
      },
      {
        id: "STU-2026-005",
        fullName: "Olivia Hayes",
        age: 17,
        grade: "12th Grade",
        department: "Humanities Section",
        email: "olivia.hayes@example.com",
        phone: "+1 555-210-1005",
        address: "302 Willow Drive, Seattle, WA",
        bio: "Olivia has a strong passion for literature, public speaking, and debate. She enjoys reading classic novels and mentoring younger students in communication skills.",
        subjects: ["English", "World History", "Debate", "Public Speaking", "Critical Thinking"],
        photo: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=900&q=80",
        gallery: [
          "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1517365830460-955ce3ccd263?auto=format&fit=crop&w=900&q=80"
        ]
      },
      {
        id: "STU-2026-006",
        fullName: "Ethan Brooks",
        age: 15,
        grade: "10th Grade",
        department: "Engineering Section",
        email: "ethan.brooks@example.com",
        phone: "+1 555-210-1006",
        address: "17 Pine Crest, Phoenix, AZ",
        bio: "Ethan is enthusiastic about mechanical systems, model building, and mathematics. He likes hands-on projects and often participates in engineering club activities.",
        subjects: ["Mathematics", "Engineering Basics", "Physics", "Technical Drawing", "Problem Solving"],
        photo: "https://images.unsplash.com/photo-1507591064344-4c6ce005b128?auto=format&fit=crop&w=900&q=80",
        gallery: [
          "https://images.unsplash.com/photo-1507591064344-4c6ce005b128?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&w=900&q=80"
        ]
      },
      {
        id: "STU-2026-007",
        fullName: "Ava Mitchell",
        age: 16,
        grade: "11th Grade",
        department: "Languages Section",
        email: "ava.mitchell@example.com",
        phone: "+1 555-210-1007",
        address: "560 Lake View Street, Portland, OR",
        bio: "Ava enjoys learning languages and exploring world cultures. She is active in language club activities and likes helping classmates improve pronunciation and writing.",
        subjects: ["English", "French", "Spanish", "Cultural Studies", "Writing Skills"],
        photo: "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80",
        gallery: [
          "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1512316609839-ce289d3eba0a?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=900&q=80"
        ]
      },
      {
        id: "STU-2026-008",
        fullName: "James Walker",
        age: 17,
        grade: "12th Grade",
        department: "Mathematics Section",
        email: "james.walker@example.com",
        phone: "+1 555-210-1008",
        address: "742 Hillcrest Avenue, Boston, MA",
        bio: "James is a focused mathematics student who enjoys statistics, calculus, and academic competitions. He is known for his consistency, discipline, and analytical thinking.",
        subjects: ["Calculus", "Statistics", "Physics", "Logic", "Data Analysis"],
        photo: "https://images.unsplash.com/photo-1502767089025-6572583495b0?auto=format&fit=crop&w=900&q=80",
        gallery: [
          "https://images.unsplash.com/photo-1502767089025-6572583495b0?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80",
          "https://images.unsplash.com/photo-1496345965480-90d19731e543?auto=format&fit=crop&w=900&q=80"
        ]
      }
    ];

    /* ==========================================
       DOM References
    ========================================== */
    var galleryView = document.getElementById("galleryView");
    var detailsView = document.getElementById("detailsView");
    var studentsGrid = document.getElementById("studentsGrid");
    var studentDetailsContainer = document.getElementById("studentDetailsContainer");
    var studentSearchInput = document.getElementById("studentSearchInput");
    var noResultsMessage = document.getElementById("noResultsMessage");
    var backButton = document.getElementById("backButton");

    /* ==========================================
       Render student cards in the main gallery
    ========================================== */
    function renderStudentCards(studentList) {
      studentsGrid.innerHTML = "";

      if (!studentList.length) {
        noResultsMessage.classList.remove("hidden");
        return;
      }

      noResultsMessage.classList.add("hidden");

      for (var i = 0; i < studentList.length; i++) {
        var student = studentList[i];

        var card = document.createElement("div");
        card.className = "student-card";
        card.setAttribute("data-student-id", student.id);
        card.setAttribute("tabindex", "0");
        card.setAttribute("role", "button");
        card.setAttribute("aria-label", "Open details for " + student.fullName);

        card.innerHTML =
          '<div class="student-card-image">' +
            '<img src="' + student.photo + '" alt="' + student.fullName + '">' +
          '</div>' +
          '<div class="student-card-body">' +
            '<div class="student-name">' + student.fullName + '</div>' +
          '</div>';

        addCardEvents(card, student.id);
        studentsGrid.appendChild(card);
      }
    }

    /* ==========================================
       Add click and keyboard support to cards
    ========================================== */
    function addCardEvents(cardElement, studentId) {
      cardElement.onclick = function () {
        openStudentDetails(studentId);
      };

      cardElement.onkeydown = function (event) {
        var key = event.key || event.keyCode;
        if (key === "Enter" || key === " " || key === 13 || key === 32) {
          event.preventDefault();
          openStudentDetails(studentId);
        }
      };
    }

    /* ==========================================
       Open the details view for a selected student
       This simulates page switching inside one file
    ========================================== */
    function openStudentDetails(studentId) {
      var student = findStudentById(studentId);
      if (!student) return;

      studentDetailsContainer.innerHTML = buildStudentDetailsHTML(student);

      galleryView.classList.add("hidden");
      detailsView.classList.remove("hidden");
      detailsView.classList.add("fade-in-up");

      window.scrollTo({
        top: 0,
        behavior: "smooth"
      });

      setTimeout(function () {
        detailsView.classList.remove("fade-in-up");
      }, 500);
    }

    /* ==========================================
       Return to the gallery view
    ========================================== */
    function showGalleryView() {
      detailsView.classList.add("hidden");
      galleryView.classList.remove("hidden");

      window.scrollTo({
        top: 0,
        behavior: "smooth"
      });
    }

    /* ==========================================
       Build student details HTML
    ========================================== */
    function buildStudentDetailsHTML(student) {
      var subjectsHTML = "";
      var galleryHTML = "";

      for (var i = 0; i < student.subjects.length; i++) {
        subjectsHTML += '<span class="tag-item">' + student.subjects[i] + '</span>';
      }

      for (var j = 0; j < student.gallery.length; j++) {
        galleryHTML +=
          '<div class="extra-gallery-item">' +
            '<img src="' + student.gallery[j] + '" alt="' + student.fullName + ' photo ' + (j + 1) + '">' +
          '</div>';
      }

      return (
        '<div class="profile-sidebar">' +
          '<div class="profile-main-photo">' +
            '<img src="' + student.photo + '" alt="' + student.fullName + '">' +
          '</div>' +
          '<div class="profile-sidebar-content">' +
            '<h2 class="profile-name">' + student.fullName + '</h2>' +
            '<div class="profile-subtext">' + student.department + ' &bull; ' + student.grade + '</div>' +
            '<div class="profile-contact-list">' +
              '<div class="contact-item">' +
                '<span class="contact-label">Student ID</span>' +
                '<span class="contact-value">' + student.id + '</span>' +
              '</div>' +
              '<div class="contact-item">' +
                '<span class="contact-label">Email</span>' +
                '<span class="contact-value">' + student.email + '</span>' +
              '</div>' +
              '<div class="contact-item">' +
                '<span class="contact-label">Phone</span>' +
                '<span class="contact-value">' + student.phone + '</span>' +
              '</div>' +
              '<div class="contact-item">' +
                '<span class="contact-label">Address</span>' +
                '<span class="contact-value">' + student.address + '</span>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</div>' +

        '<div class="profile-main">' +
          '<div class="profile-sections">' +
            '<div class="profile-card">' +
              '<h3>Student Information</h3>' +
              '<div class="info-grid">' +
                '<div class="info-box">' +
                  '<span class="info-label">Full Name</span>' +
                  '<span class="info-value">' + student.fullName + '</span>' +
                '</div>' +
                '<div class="info-box">' +
                  '<span class="info-label">Age</span>' +
                  '<span class="info-value">' + student.age + ' years old</span>' +
                '</div>' +
                '<div class="info-box">' +
                  '<span class="info-label">Class / Grade</span>' +
                  '<span class="info-value">' + student.grade + '</span>' +
                '</div>' +
                '<div class="info-box">' +
                  '<span class="info-label">Department / Section</span>' +
                  '<span class="info-value">' + student.department + '</span>' +
                '</div>' +
              '</div>' +
            '</div>' +

            '<div class="profile-card">' +
              '<h3>About</h3>' +
              '<p>' + student.bio + '</p>' +
            '</div>' +

            '<div class="profile-card">' +
              '<h3>Subjects / Skills</h3>' +
              '<div class="tag-list">' + subjectsHTML + '</div>' +
            '</div>' +

            '<div class="profile-card">' +
              '<h3>Extra Photo Gallery</h3>' +
              '<div class="extra-gallery">' + galleryHTML + '</div>' +
            '</div>' +
          '</div>' +
        '</div>'
      );
    }

    /* ==========================================
       Find one student by ID
    ========================================== */
    function findStudentById(studentId) {
      for (var i = 0; i < studentsData.length; i++) {
        if (studentsData[i].id === studentId) {
          return studentsData[i];
        }
      }
      return null;
    }

    /* ==========================================
       Search students by any part of the name
       Case-insensitive live filtering
    ========================================== */
    function filterStudentsByName(searchText) {
      var query = (searchText || "").toLowerCase().replace(/^\s+|\s+$/g, "");
      var filtered = [];

      for (var i = 0; i < studentsData.length; i++) {
        var name = studentsData[i].fullName.toLowerCase();
        if (name.indexOf(query) !== -1) {
          filtered.push(studentsData[i]);
        }
      }

      renderStudentCards(filtered);
    }

    /* ==========================================
       Event Listeners
    ========================================== */
    studentSearchInput.addEventListener("input", function () {
      filterStudentsByName(this.value);
    });

    backButton.addEventListener("click", function () {
      showGalleryView();
    });

    /* ==========================================
       Initial Render
    ========================================== */
    renderStudentCards(studentsData);
  </script>
</body>
</html>
