# Digikala.com Clone Django REST Framework TEST-DRIVEN DEVELOPMENT(TDD) Tests

## 📖 About
توسعه فرضی وبسایت های large-scale e-commerce platform مانند سایت دیجی کالا با استفاده از جنگو نیازمند پیاده سازی معماری است که باید robust, reliable و maintainable باشد. بنابراین تست نویسی یا در پیش گرفتن متودولوژی TDD می تواند یک گزینه مناسب برای رسیدن به هدف باشد. در این ریپو تلاش کردیم مجموعه وسیع و کاملی از تست ها که توسعه یک وبسایت بزرگ مانند دیجی کالا به آن نیاز دارد را پوشش دهیم.

هدف اولیه این بوده است که coverage تست ها بالای 90 درصد باشد.

همچنین به دلیل رویکرد آموزشی این ریپو فقط قسمت تست های پروژه پیاده سازی و  از Pytest, TestCase و APITestCase استفاده شده است.


## 🛠 Tech Stack
- **Backend**: Django, Django REST Framework
- **Testing**: Pytest, coverage.py, mutmut, Locust


## ✨ Test Types Coverage
- **Unit Tests**: Verify the functionality of individual components (models, serializers, services) in isolation.
- **Integration Tests**: Ensure that different components of the application work together as expected.
- **Mutation Tests**: Evaluate the quality of the existing test suite by introducing small, deliberate faults into the source code and checking if the tests fail.
- **Chaos Tests**: To build confidence in the system's capability to withstand turbulent and unexpected conditions in production.
- **Compatibility Tests**: Ensure the API works correctly with different clients, browsers, and configurations.
- **Infrastructure Tests**: Verify the health and configuration of the application's underlying infrastructure components.
- **Data Integrity Tests**: Ensure that data remains accurate and consistent after operations.
- **Acceptance Tests**: Validate that the system meets the business requirements from a user's perspective.
- **Regression Tests**: Ensure that new code changes do not break existing functionality. These are often tests written to replicate a bug that has been fixed.
- **Performance Tests**: Evaluate the responsiveness, stability, and scalability of the application under a given workload.
- **Security Tests**: Identify and fix security vulnerabilities in the application.
- **System/End-to-End Tests**: Test the complete application in an environment that closely resembles production, including integrations with external services.
