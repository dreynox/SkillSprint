# Faculty of Science and Technology
## Department of Engineering Sciences
### Applied Science and Engineering Project
### Academic Year 2025-26 Sem II

## Project Title: SkillSprint - Competitive Coding and Hackathon Portal
**Name of Mentor:** To be filled by the project guide

### Team Members
| Name | Roll No. | PRN No. |
|---|---:|---:|
| To be filled |  |  |
| To be filled |  |  |
| To be filled |  |  |

**Division:** To be filled
**Batch:** To be filled
**Class:** To be filled
**Branch:** To be filled

---

## Index
1. Problem Statement
2. Objective
3. Methodology
4. Results and Analysis
5. Global / National Relevance
6. Future Scope
7. References
8. Conclusion

---

## 1. Problem Statement

Traditional learning and assessment platforms often handle coding practice, quizzes, contests, and hackathon participation as separate tools. Because of this fragmentation, students must switch between multiple systems to practice programming, attempt tests, track progress, and participate in competitions. This reduces convenience and makes the learning workflow less efficient.

Another major issue is the lack of a single platform that supports both learning and evaluation in a structured way. In many cases, students can access questions or contests, but they do not get a unified experience that combines authentication, role-based access, code execution, scoring, leaderboard tracking, and event management. As a result, the process becomes inconsistent and harder to monitor.

Manual administration of quizzes, contests, and student submissions also creates delays. Without a centralized backend, maintaining question banks, managing user submissions, and publishing results becomes time-consuming. Students may not receive timely feedback, and administrators may find it difficult to manage large numbers of users efficiently.

There is also a growing need for a scalable academic platform that can support multiple programming languages, real-time evaluation, and secure user management. These requirements highlight the need for a modern full-stack solution that improves engagement, simplifies management, and creates a better environment for competitive learning.

---

## 2. Objective

The main objective of this project is to develop an integrated full-stack platform that supports competitive programming, quiz-based assessment, and hackathon management in one place.

1. To design a centralized coding and learning portal:
   The project aims to bring coding practice, contests, quizzes, and hackathons together in a single web-based system so that students can access all core learning activities from one platform.

2. To implement secure authentication and role-based access:
   The system supports user registration and login, with separate access paths for students and administrators. This ensures safe access control and proper management of platform features.

3. To provide multi-language code execution support:
   A compiler engine is integrated to allow users to run and test code in multiple programming languages, improving the practical value of the platform for learners.

4. To automate quiz, contest, and submission workflows:
   The platform manages question banks, test attempts, contest submissions, and score processing through a structured backend, reducing manual effort and improving response time.

5. To improve engagement through rankings and progress tracking:
   Leaderboards, user profiles, and result tracking are included so that students can monitor performance, compare outcomes, and stay motivated.

6. To create an admin-friendly management system:
   Administrators can manage content, users, contests, quizzes, and published results from a dedicated interface, making the system easier to maintain.

---

## 3. Methodology

The project is developed in multiple stages to ensure proper design, implementation, testing, and deployment of the SkillSprint platform.

### 3.1 System Design

The first stage focuses on the overall architecture of the application. SkillSprint is designed as a full-stack web platform with a frontend interface, backend API layer, and relational database. The frontend handles user interaction, while the backend manages authentication, contest logic, quiz processing, and data persistence.

The system is organized into modules such as authentication, quiz management, contest management, compiler integration, leaderboard handling, and admin operations. This modular design makes the application easier to extend and maintain.

### 3.2 Technology Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** FastAPI with Python
- **Database:** SQLite for local development and PostgreSQL for deployment
- **ORM:** SQLAlchemy
- **Deployment Support:** Docker and Render
- **Code Execution:** Integrated compiler engine with multiple language support

### 3.3 Component Integration

In this stage, the major application components are connected together. The frontend pages communicate with backend APIs, and the backend exchanges data with the database through SQLAlchemy models. Authentication routes, quiz routes, contest routes, and compiler routes are integrated so that each user action is handled through a defined API flow.

The database stores user information, tests, questions, quiz submissions, contests, contest problems, and contest submissions. This structure supports reliable tracking of activities and results across the platform.

### 3.4 Development and Implementation

The implementation stage includes backend route development, schema definition, page creation, and feature testing. The backend provides endpoints for registration, login, quiz attempts, contest creation, contest submissions, and compiler execution. The frontend presents pages for users to interact with quizzes, contests, dashboards, and related features.

The code execution component supports several programming languages, including C, C++, Python, JavaScript, Java, PHP, Go, Rust, and R. Web-oriented languages such as HTML, CSS, React, and TypeScript are also recognized in preview-based workflows.

### 3.5 Testing and Validation

The final stage involves testing the platform to confirm that authentication works correctly, quiz results are stored accurately, contest submissions are processed properly, and the compiler engine returns expected output. Database persistence, API responses, and deployment configuration are also validated to ensure stable application behavior.

---

## 4. Results and Analysis

The SkillSprint platform was successfully developed as a unified competitive learning system. The final implementation demonstrates that a single application can support coding practice, assessment, contests, and event participation in a structured way.

### 4.1 Successfully Implemented Features

- User registration and login with role-based access
- Quiz system for test creation, question delivery, and score storage
- Contest module for problem listing, submission handling, and result tracking
- Compiler integration for multi-language code execution
- Admin management for tests, contests, and platform oversight
- User dashboards for monitoring activity and performance
- Public ranking and leaderboard-style progress display
- Badge-based motivation through points-derived performance tiers (Starter, Intermediate, Advanced, Pro, Elite)
- Live contest timing indicators and periodic leaderboard refresh for near real-time participation tracking

### 4.2 Technical Analysis

The application is organized into a modular backend structure, which improves maintainability and makes the codebase easier to extend. Database models are normalized to support efficient storage of users, tests, questions, contests, and submissions.

The system also provides a scalable foundation for future enhancements. Because the backend is API-driven, new features can be added without redesigning the full application. This is particularly useful for adding advanced analytics, real-time updates, or collaboration features later.

### 4.3 Observed Benefits

- Students can access learning, evaluation, and competition features from one platform.
- Administrators can manage academic activities with less manual effort.
- The platform improves consistency in evaluation and result tracking.
- Integrated code execution gives users practical programming feedback.
- The system supports both local development and deployment-oriented workflows.

### 4.4 Project Summary Metrics

| Component | Status |
|---|---|
| Authentication System | Implemented |
| Quiz Module | Implemented |
| Contest Module | Implemented |
| Compiler Integration | Implemented |
| Admin Management | Implemented |
| Database Persistence | Implemented |
| Multi-language Support | Implemented |
| Badge-based Motivation | Implemented |
| Live Ranking Refresh | Implemented |
| Deployment Support | Implemented |

---

## 5. Global / National Relevance

SkillSprint is relevant at both global and national levels because it addresses a common educational challenge: the need for accessible, structured, and engaging technical skill development.

### Global Relevance

- It supports modern digital learning through a web-based platform.
- It combines assessment, practice, and competition in one system.
- It helps learners build programming skills in an environment that reflects real-world problem solving.
- It can be used as a foundation for scalable academic and training platforms.

### National Relevance (India)

- India has a large population of students who need affordable and accessible technical learning tools.
- Competitive programming and coding practice are increasingly important for employability in the IT sector.
- A platform like SkillSprint can support skill development in colleges, training centers, and self-learning environments.
- The project aligns with the broader goal of improving digital education and technical readiness.

### Practical Impact

This project demonstrates how a low-cost, software-based solution can improve learning, assessment, and competition management. It can be adopted in educational institutions to simplify coding practice, tests, and event organization while improving student engagement.

---

## 6. Future Scope

The current version of SkillSprint provides a strong base for a full-stack competitive learning platform. It can be expanded further to improve interactivity, intelligence, and scalability.

- **Real-time collaboration:** Multiple users can work together on problems or share code in live sessions.
- **AI-based recommendations:** The system can suggest questions, contests, or learning paths based on user performance.
- **Mobile application:** A dedicated mobile app can provide easier access to quizzes, contests, and notifications.
- **Advanced analytics:** Detailed dashboards can show learning trends, weak areas, and progress summaries.
- **Advanced live contest monitoring:** Admins can monitor contest activity and submission patterns with richer event analytics and alerts.
- **Cloud scaling:** The platform can be expanded to support larger user bases across colleges and institutions.
- **Interview preparation module:** Dedicated problem sets and mock assessments can be added for placement support.

---

## 7. References

The following references are related to online programming education platforms, automated evaluation, gamification, learning analytics, and the technologies used in SkillSprint.

1. Ala-Mutka, K. M. (2005). A survey of automated assessment approaches for programming assignments. Computer Science Education, 15(2), 83-102.
2. Douce, C., Livingstone, D., and Orwell, J. (2005). Automatic test-based assessment of programming: A review. Journal on Educational Resources in Computing, 5(3), Article 4.
3. Keuning, H., Jeuring, J., and Heeren, B. (2018). A systematic literature review of automated feedback generation for programming exercises. ACM Transactions on Computing Education, 19(1), Article 3.
4. Piech, C., Huang, J., Nguyen, A., Phulsuksombati, M., Sahami, M., and Guibas, L. J. (2015). Learning program embeddings to propagate feedback on student code. In Proceedings of the 32nd International Conference on Machine Learning (ICML).
5. Deterding, S., Dixon, D., Khaled, R., and Nacke, L. (2011). From game design elements to gamefulness: Defining gamification. In Proceedings of the 15th International Academic MindTrek Conference.
6. Hamari, J., Koivisto, J., and Sarsa, H. (2014). Does gamification work? A literature review of empirical studies on gamification. In Proceedings of the 47th Hawaii International Conference on System Sciences (HICSS).
7. Romero, C., and Ventura, S. (2010). Educational data mining: A review of the state of the art. IEEE Transactions on Systems, Man, and Cybernetics, Part C, 40(6), 601-618.
8. Siemens, G., and Long, P. (2011). Penetrating the fog: Analytics in learning and education. EDUCAUSE Review, 46(5), 30-32.
9. FastAPI Documentation. https://fastapi.tiangolo.com/
10. SQLAlchemy Documentation. https://docs.sqlalchemy.org/
11. PostgreSQL Documentation. https://www.postgresql.org/docs/
12. OWASP Foundation. OWASP Top 10 Web Application Security Risks. https://owasp.org/www-project-top-ten/

---

## 8. Conclusion

SkillSprint successfully demonstrates the development of a unified competitive coding and hackathon portal that combines authentication, quizzes, contests, code execution, and administrative control in one system. The project addresses the limitations of fragmented learning tools by providing a structured and integrated platform for students and administrators.

The application improves accessibility, usability, and engagement by allowing users to practice coding, attempt quizzes, participate in contests, and track results within a single environment. It also gives administrators a practical way to manage academic activities and content efficiently.

Overall, the project shows how modern web technologies can be used to build a scalable and useful educational platform. With future enhancements such as AI support, mobile access, and live collaboration, SkillSprint can evolve into a more advanced system for technical learning and competitive programming.
