module abs_diff_i18432_o9216(a,b,r);
input [9215:0] a,b;
output [9215:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
