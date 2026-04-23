module abs_diff_i61440_o30720(a,b,r);
input [30719:0] a,b;
output [30719:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
