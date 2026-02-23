module abs_diff_i484_o242(a,b,r);
input [241:0] a,b;
output [241:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
