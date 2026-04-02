module abs_diff_i728_o364(a,b,r);
input [363:0] a,b;
output [363:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
