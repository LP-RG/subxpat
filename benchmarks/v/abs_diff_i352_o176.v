module abs_diff_i352_o176(a,b,r);
input [175:0] a,b;
output [175:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
