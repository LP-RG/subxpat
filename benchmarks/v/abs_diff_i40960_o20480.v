module abs_diff_i40960_o20480(a,b,r);
input [20479:0] a,b;
output [20479:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
