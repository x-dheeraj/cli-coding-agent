<script>
    function appendToDisplay(value) {
        let display = document.getElementById('display').value;
        display += value;
        document.getElementById('display').value = display;
    }

    function clearDisplay() {
        document.getElementById('display').value = '';
    }

    function calculate() {
        try {
            let result = eval(document.getElementById('display').value);
            document.getElementById('display').value = result.toString().replace('.0', '.');
        } catch (err) {
            document.getElementById('display').value = 'Error';
        }
    }
</script>