NoteEditorComponent = {
    props: ['title', 'content', 'errorMessage', 'successMessage'],
    emits: ['save', 'cancel'],
    data() {
        return {mTitle: this.title, mContent: this.content, images: new Map()}
    },
    components: {CodeMirrorComponent},
    template: `
        <form @keydown="save_by_button">
            <div class="form-group" id="title-group">
                <div class="form-floating">
                    <input name="title" v-model="mTitle" style="width:99%;border-bottom-left-radius: 0;border-bottom-right-radius: 0;" class="form-control" placeholder="Заголовок" id="title-field">
                    <label for="title-field" class="form-label">Заголовок заметки</label>
                </div>
            </div>
            <div class="form-group" id="content-group" style="text-align: left;">
               <code-mirror-component :on_code_mirror_ready="on_code_mirror_ready" v-model="mContent" name="content" mode="markdown" id="content-field" class="form-control"></code-mirror-component>
            </div>
            <br>
            <div :class="{'d-none': !errorMessage}">
                <span>[[ errorMessage ]]</span>
                <br>
            </div>
            <div :class="{'d-none': !successMessage}">
                <span>[[ successMessage ]]</span>
                <br>
            </div>
            <input type="button" value="Сохранить" @click="save" class="btn btn-primary">
            &nbsp;
            <input type="button" value="Отменить" @click="cancel" class="btn btn-secondary">
            &nbsp;
        </form>
    `,
    methods: {
        save_by_button(event) {
            if (event.code == 'KeyS' && event.ctrlKey) {
                this.$emit('save', event, this.mTitle, this.mContent, this.images, false);
                event.preventDefault();
            }
        },
        save(event) {
            this.$emit('save', event, this.mTitle, this.mContent, this.images, true);
        },
        cancel(event) {
            this.$emit('cancel', event, this, this.mTitle, this.mContent);
        },
        on_code_mirror_ready(cm) {
            function buf2hex(buffer) { // buffer is an ArrayBuffer
                return [...new Uint8Array(buffer)]
                    .map(x => x.toString(16).padStart(2, '0'))
                    .join('');
            }

            self = this;
            cm.on(
                'paste',
                function(doc, event) {
                    allowed_types = new Set(['image/jpeg', 'image/png', 'image/svg+xml']);
                    // https://stackoverflow.com/questions/6333814/how-does-the-paste-image-from-clipboard-functionality-work-in-gmail-and-google-c
                    var items = (event.clipboardData || event.originalEvent.clipboardData).items;
                    for (var index in items) {
                        var item = items[index];
                        if (item.kind == 'file') {
                            let file = item.getAsFile();
                            if (!allowed_types.has(file.type)) {
                                console.log('not allowed type: ', file.type);
                                continue;
                            }
                            if (file.size / 1024 > 1024) {  // allow 1024 KB
                                console.log('not allowed size: ', file.size / 1024);
                                continue;
                            }
                            var reader = new FileReader();
                            let cursor = cm.getCursor();
                            reader.onload = function (event) {
                                let hash = crypto.subtle.digest('sha-256', reader.result);
                                hash.then(
                                    function(result){
                                        let hexed_hash = buf2hex(result) + '.' + file.type.split('/')[1];
                                        self.images.set(hexed_hash, file);
                                        cm.replaceRange('!['+file.name+']('+hexed_hash+')', cursor, cursor);
                                    }
                                );
                                event.preventDefault();
                            }
                            reader.readAsArrayBuffer(file);
                        }
                    }
                },
            );
        },
    },
}
