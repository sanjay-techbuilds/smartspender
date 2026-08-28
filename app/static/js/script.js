document.addEventListener("DOMContentLoaded", function () {
    // Smooth looping for background video
    const video = document.querySelector(".bg-video");

    if (video) {
        function smoothLoop() {
            if (video.currentTime >= video.duration - 0.1) {
                video.currentTime = 0;
                video.play();
            }
            requestAnimationFrame(smoothLoop);
        }

        video.play();
        requestAnimationFrame(smoothLoop);
    }

    // Simulating expenseData (Replace this with actual data fetching)
    const expenseData = [
        { category: "Food", total: 120 },
        { category: "Transport", total: 80 },
        { category: "Entertainment", total: 50 },
        { category: "Bills", total: 200 }
    ];

    console.log("Expense Data:", expenseData);

    if (!expenseData || expenseData.length === 0) {
        console.error("No expense data available for visualization.");
        return;
    }

    const labels = expenseData.map(item => item.category);
    const values = expenseData.map(item => item.total);

    const ctx = document.getElementById('expenseChart').getContext('2d');

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: 'Expenses',
                data: values,
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });

    // 🔥 Password Match Validation for Register Page
    const registerForm = document.querySelector(".auth-form");
    if (registerForm) {
        registerForm.addEventListener("submit", function (event) {
            const password = document.querySelector("input[name='password']").value;
            const confirmPassword = document.querySelector("input[name='confirm_password']").value;

            if (password !== confirmPassword) {
                event.preventDefault();  // Stop form submission
                alert("Passwords do not match! Please check again.");
            }
        });
    }
});
