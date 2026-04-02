module abs_diff_i260_o130(a,b,r);
input [129:0] a,b;
output [129:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
