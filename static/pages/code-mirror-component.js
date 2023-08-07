CodeMirrorComponent = {
    props: ['modelValue', 'mode'],
    emits: ['update:modelValue'],
    data() {
        console.log(this.$el);
        return {
            noteCodeMirror: undefined,
        };
    },
    computed: {
        value: {
            get() {
                return this.modelValue;
            },
            set(value) {
                this.$emit('update:modelValue', value);
            },
        }
    },
    template: `<textarea v-model="value"></textarea>`,
    mounted() {
        this.noteCodeMirror = CodeMirror.fromTextArea(
            this.$el,
            {
                theme: "default",
                lineNumbers: true,
                mode: this.mode,
                lineWrapping: true,
                extraKeys: {"Enter": "newlineAndIndentContinueMarkdownList"},
            },
        );
        let self = this;
        this.noteCodeMirror.getDoc().on(
            'change',
            function(doc) {self.value = doc.getValue();},
        );
    },
}
