const ToggleField = {
    props: ["id", "value", "name"],
    emits: ['focus', 'blur'],
    template: `
<span>
<span class="el_sign" @click="focus" style="display: inline-block; cursor: pointer; width: 100%;" :class="{'d-none': is_edit}">[[ mvalue ]]</span>
<input v-model.trim="mvalue" :name="name" @blur="blur" class="el_field" :class="{'d-none': !is_edit}"/>
</span>`,
    data() {
        return {mvalue: this.value, mid: this.id, previous_value: this.value, is_edit: false};
    },
    methods: {
        focus(event) {
            this.is_edit = true;
            let field = this.$el.querySelector('.el_field');
            this.previous_value = this.mvalue;
            self = this;
            setTimeout(function() {
                field.focus();
                self.$emit('focus', self);
            }, 20);
        },
        blur(event) {
            this.is_edit = false;
            if (this.mid) {
                if (this.mvalue) {
                    if (this.mvalue != this.previous_value) {
                        this.$emit('blur', this, true, true);
                    }
                } else {
                    this.mvalue = this.previous_value;
                }
            } else {
                if (this.mvalue) {
                    this.$emit('blur', this, false, true);
                } else {
                    this.mvalue = this.previous_value;
                    this.$emit('blur', this, false, false);
                }
            }
        },
    },
}
