CodeMirrorComponent = {
    inheritAttrs: false,
    props: ['modelValue', 'mode'],
    emits: ['update:modelValue'],
    data() {
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
    template: `<div><textarea v-model="value" v-bind="$attrs"></textarea></div>`,
    mounted() {
        this.noteCodeMirror = CodeMirror.fromTextArea(
            this.$el.children[0],
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
