const changePhoto = document.getElementById("changePhoto");
const profileInput = document.getElementById("profile_picture");
const preview = document.getElementById("preview");

changePhoto.addEventListener("click", () => {
    profileInput.click();
});

profileInput.addEventListener("change", function () {

    const file = this.files[0];

    if(file){

        const reader = new FileReader();

        reader.onload = function(e){

            preview.src = e.target.result;

        }

        reader.readAsDataURL(file);

    }

});