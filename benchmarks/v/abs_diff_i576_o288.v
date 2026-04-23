module abs_diff_i576_o288(a,b,r);
input [287:0] a,b;
output [287:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
