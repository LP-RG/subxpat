module abs_diff_i676_o338(a,b,r);
input [337:0] a,b;
output [337:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
