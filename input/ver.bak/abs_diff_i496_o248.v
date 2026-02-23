module abs_diff_i496_o248(a,b,r);
input [247:0] a,b;
output [247:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
