function toggleAvailabilityFields(checkbox) {
    const day = checkbox.dataset.day;
    const startInput = document.getElementById(`day_${day}_start`);
    const endInput = document.getElementById(`day_${day}_end`);

    if (checkbox.checked) {
        startInput.disabled = false;
        endInput.disabled = false;
    } else {
        startInput.disabled = true;
        endInput.disabled = true;
        startInput.value = "";
        endInput.value = "";
    }
}

document.querySelectorAll(".availability-checkbox").forEach(function (checkbox) {
    toggleAvailabilityFields(checkbox);

    checkbox.addEventListener("change", function () {
        toggleAvailabilityFields(checkbox);
    });
});


document.querySelectorAll(".booking-slot").forEach(function (button) {
    button.addEventListener("click", function () {
        document.querySelectorAll(".booking-slot").forEach(function (slotButton) {
            slotButton.classList.remove("booking-slot-selected");
        });

        button.classList.add("booking-slot-selected");

        const startTime = button.dataset.startTime;
        const displayTime = button.dataset.displayTime;

        document.getElementById("selected-start-time").value = startTime;
        document.getElementById("selected-display-time").textContent = displayTime;
        document.getElementById("booking-summary").style.display = "block";
    });
});
